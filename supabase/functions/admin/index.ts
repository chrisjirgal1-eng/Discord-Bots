// Admin API for the Zenthra team dashboard.
// Every call authenticates with the x-admin-code header checked against the
// sha256 hash stored in app_config (key: admin_code_hash). Until that row is
// seeded, every call is rejected — locked by default, never open by default.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-admin-code",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// 32-char alphabet without lookalikes (0/O, 1/I/L). 8 chars = 40 bits.
const CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";

const MEMBER_FIELDS = [
  "discord_username",
  "display_name",
  "timezone",
  "schedule",
  "role",
  "active",
];
const TASK_FIELDS = ["title", "description", "due_date", "sort_order", "status"];

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

function normalizeCode(code: string): string {
  return (code || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
}

async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text),
  );
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function getConfig(keys: string[]): Promise<Record<string, string>> {
  const { data } = await supabase
    .from("app_config")
    .select("key, value")
    .in("key", keys);
  const out: Record<string, string> = {};
  for (const row of data ?? []) out[row.key] = row.value;
  return out;
}

async function authAdmin(req: Request): Promise<boolean> {
  const code = (req.headers.get("x-admin-code") || "").trim();
  if (!code) return false;
  const cfg = await getConfig(["admin_code_hash"]);
  if (!cfg.admin_code_hash) return false;
  return safeEqual(await sha256Hex(code), cfg.admin_code_hash);
}

function generateCode(): string {
  const buf = new Uint8Array(8);
  crypto.getRandomValues(buf);
  let s = "";
  for (let i = 0; i < 8; i++) s += CODE_ALPHABET[buf[i] % CODE_ALPHABET.length];
  return s.slice(0, 4) + "-" + s.slice(4);
}

function validTimezone(tz: string): boolean {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: tz });
    return true;
  } catch {
    return false;
  }
}

// deno-lint-ignore no-explicit-any
function pick(body: any, fields: string[]) {
  const out: Record<string, unknown> = {};
  for (const f of fields) if (f in body) out[f] = body[f];
  return out;
}

// deno-lint-ignore no-explicit-any
async function sendDiscordPing(task: any, member: any): Promise<boolean> {
  const cfg = await getConfig(["discord_webhook_url", "chris_discord_id"]);
  if (!cfg.discord_webhook_url) return false;
  const mention = cfg.chris_discord_id ? `<@${cfg.chris_discord_id}> ` : "";
  const name = member.display_name || member.discord_username;
  const payload = {
    content: `${mention}Task completed ✅`,
    allowed_mentions: cfg.chris_discord_id
      ? { users: [cfg.chris_discord_id] }
      : { parse: [] },
    embeds: [
      {
        title: task.title,
        description: `Completed by **${name}** (@${member.discord_username})`,
        image: task.proof_image_url ? { url: task.proof_image_url } : undefined,
        timestamp: new Date().toISOString(),
        color: 5763719,
      },
    ],
  };
  try {
    const res = await fetch(cfg.discord_webhook_url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.ok;
  } catch (err) {
    console.error("discord ping failed:", err);
    return false;
  }
}

async function listAll(): Promise<Response> {
  const { data: members, error: mErr } = await supabase
    .from("members")
    .select("id, discord_username, display_name, timezone, schedule, role, active, created_at")
    .order("created_at");
  const { data: tasks, error: tErr } = await supabase
    .from("tasks")
    .select("*")
    .order("sort_order")
    .order("created_at");
  if (mErr || tErr) return json(500, { error: "Could not load the board." });
  const cfg = await getConfig(["discord_webhook_url"]);
  return json(200, { members, tasks, webhook_configured: !!cfg.discord_webhook_url });
}

// deno-lint-ignore no-explicit-any
async function addMember(body: any): Promise<Response> {
  const username = String(body.discord_username || "").trim();
  if (!username) return json(400, { error: "Discord username is required." });
  const timezone = String(body.timezone || "America/Chicago");
  if (!validTimezone(timezone)) {
    return json(400, { error: "Unknown timezone." });
  }
  const code = generateCode();
  const { data: member, error } = await supabase
    .from("members")
    .insert({
      discord_username: username,
      display_name: body.display_name || null,
      timezone,
      schedule: body.schedule || {},
      role: body.role || null,
      access_code_hash: await sha256Hex(normalizeCode(code)),
    })
    .select("id, discord_username, display_name, timezone, schedule, role, active, created_at")
    .single();
  if (error) {
    if (error.code === "23505") {
      return json(400, { error: "That Discord username is already on the board." });
    }
    console.error("add_member failed:", error);
    return json(500, { error: "Could not add the member." });
  }
  return json(200, { member, access_code: code });
}

// deno-lint-ignore no-explicit-any
async function updateMember(body: any): Promise<Response> {
  if (!body.member_id) return json(400, { error: "Missing member." });
  const fields = pick(body, MEMBER_FIELDS);
  if ("discord_username" in fields) {
    fields.discord_username = String(fields.discord_username || "").trim();
    if (!fields.discord_username) {
      return json(400, { error: "Discord username is required." });
    }
  }
  if ("timezone" in fields && !validTimezone(String(fields.timezone))) {
    return json(400, { error: "Unknown timezone." });
  }
  if (Object.keys(fields).length === 0) {
    return json(400, { error: "Nothing to update." });
  }
  const { data: member, error } = await supabase
    .from("members")
    .update(fields)
    .eq("id", body.member_id)
    .select("id, discord_username, display_name, timezone, schedule, role, active, created_at")
    .maybeSingle();
  if (error) {
    if (error.code === "23505") {
      return json(400, { error: "That Discord username is already on the board." });
    }
    console.error("update_member failed:", error);
    return json(500, { error: "Could not update the member." });
  }
  if (!member) return json(404, { error: "Member not found." });
  return json(200, { member });
}

// deno-lint-ignore no-explicit-any
async function regenCode(body: any): Promise<Response> {
  if (!body.member_id) return json(400, { error: "Missing member." });
  const code = generateCode();
  const { data: member } = await supabase
    .from("members")
    .update({ access_code_hash: await sha256Hex(normalizeCode(code)) })
    .eq("id", body.member_id)
    .select("id, discord_username")
    .maybeSingle();
  if (!member) return json(404, { error: "Member not found." });
  return json(200, { member, access_code: code });
}

// deno-lint-ignore no-explicit-any
async function createTask(body: any): Promise<Response> {
  if (!body.member_id) return json(400, { error: "Missing member." });
  const title = String(body.title || "").trim();
  if (!title) return json(400, { error: "Task title is required." });
  const { data: task, error } = await supabase
    .from("tasks")
    .insert({
      member_id: body.member_id,
      title,
      description: body.description || null,
      due_date: body.due_date || null,
      sort_order: Number(body.sort_order) || 0,
    })
    .select()
    .single();
  if (error) {
    console.error("create_task failed:", error);
    return json(400, { error: "Could not create the task." });
  }
  return json(200, { task });
}

// deno-lint-ignore no-explicit-any
async function updateTask(body: any): Promise<Response> {
  if (!body.task_id) return json(400, { error: "Missing task." });
  const fields = pick(body, TASK_FIELDS);
  if ("title" in fields) {
    fields.title = String(fields.title || "").trim();
    if (!fields.title) return json(400, { error: "Task title is required." });
  }
  if ("status" in fields) {
    if (fields.status !== "open") {
      // Completion always goes through the member flow so proof stays mandatory.
      return json(400, { error: "Tasks are completed by the member with a proof picture." });
    }
    Object.assign(fields, {
      proof_image_path: null,
      proof_image_url: null,
      completed_at: null,
      ping_sent_at: null,
    });
  }
  if (Object.keys(fields).length === 0) {
    return json(400, { error: "Nothing to update." });
  }
  const { data: existing } = await supabase
    .from("tasks")
    .select("proof_image_path")
    .eq("id", body.task_id)
    .maybeSingle();
  if (!existing) return json(404, { error: "Task not found." });
  const { data: task, error } = await supabase
    .from("tasks")
    .update(fields)
    .eq("id", body.task_id)
    .select()
    .maybeSingle();
  if (error || !task) {
    console.error("update_task failed:", error);
    return json(400, { error: "Could not update the task." });
  }
  if ("status" in fields && existing.proof_image_path) {
    await supabase.storage.from("proofs").remove([existing.proof_image_path]);
  }
  return json(200, { task });
}

// deno-lint-ignore no-explicit-any
async function deleteTask(body: any): Promise<Response> {
  if (!body.task_id) return json(400, { error: "Missing task." });
  const { data: task } = await supabase
    .from("tasks")
    .select("id, proof_image_path")
    .eq("id", body.task_id)
    .maybeSingle();
  if (!task) return json(404, { error: "Task not found." });
  if (task.proof_image_path) {
    await supabase.storage.from("proofs").remove([task.proof_image_path]);
  }
  const { error } = await supabase.from("tasks").delete().eq("id", body.task_id);
  if (error) {
    console.error("delete_task failed:", error);
    return json(500, { error: "Could not delete the task." });
  }
  return json(200, { ok: true });
}

// deno-lint-ignore no-explicit-any
async function resendPing(body: any): Promise<Response> {
  if (!body.task_id) return json(400, { error: "Missing task." });
  const { data: task } = await supabase
    .from("tasks")
    .select("*")
    .eq("id", body.task_id)
    .maybeSingle();
  if (!task) return json(404, { error: "Task not found." });
  if (task.status !== "done") {
    return json(400, { error: "Task is not completed yet." });
  }
  const { data: member } = await supabase
    .from("members")
    .select("discord_username, display_name")
    .eq("id", task.member_id)
    .maybeSingle();
  const pinged = await sendDiscordPing(task, member || {});
  if (pinged) {
    await supabase
      .from("tasks")
      .update({ ping_sent_at: new Date().toISOString() })
      .eq("id", task.id);
  }
  return json(200, { ping_sent: pinged });
}

async function testPing(): Promise<Response> {
  const cfg = await getConfig(["discord_webhook_url", "chris_discord_id"]);
  if (!cfg.discord_webhook_url) {
    return json(400, { error: "No Discord webhook configured yet." });
  }
  const mention = cfg.chris_discord_id ? `<@${cfg.chris_discord_id}> ` : "";
  try {
    const res = await fetch(cfg.discord_webhook_url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: `${mention}Zenthra task dashboard is connected. Completion pings will land here. ⚡`,
        allowed_mentions: cfg.chris_discord_id
          ? { users: [cfg.chris_discord_id] }
          : { parse: [] },
      }),
    });
    return json(200, { ping_sent: res.ok });
  } catch (err) {
    console.error("test ping failed:", err);
    return json(200, { ping_sent: false });
  }
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json(405, { error: "POST only." });
  try {
    if (!(await authAdmin(req))) {
      return json(401, { error: "Wrong admin passcode." });
    }
    let body;
    try {
      body = await req.json();
    } catch {
      return json(400, { error: "Bad request." });
    }
    switch (body.action) {
      case "list_all":
        return await listAll();
      case "add_member":
        return await addMember(body);
      case "update_member":
        return await updateMember(body);
      case "regen_code":
        return await regenCode(body);
      case "create_task":
        return await createTask(body);
      case "update_task":
        return await updateTask(body);
      case "delete_task":
        return await deleteTask(body);
      case "resend_ping":
        return await resendPing(body);
      case "test_ping":
        return await testPing();
      default:
        return json(400, { error: "Unknown action." });
    }
  } catch (err) {
    console.error("admin function error:", err);
    return json(500, { error: "Something went wrong. Try again." });
  }
});
