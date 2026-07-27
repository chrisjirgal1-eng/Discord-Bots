// Member API for the Zenthra team dashboard.
// Members authenticate with their Discord username alone (Chris's choice:
// zero-friction login for a small trusted team). Ownership checks still stop
// anyone from completing another member's task, and this function runs with
// the service role while RLS stays deny-all.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const MAX_IMAGE_BYTES = 4 * 1024 * 1024;
const EXT_BY_TYPE: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/webp": "webp",
};

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
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

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

function validTimezone(tz: string): boolean {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: tz });
    return true;
  } catch {
    return false;
  }
}

// deno-lint-ignore no-explicit-any
async function authMember(username: string): Promise<any> {
  if (!username || typeof username !== "string") return null;
  // Case-insensitive exact match; escape LIKE wildcards so ilike is exact.
  const uname = username.trim().replace(/[\\%_]/g, (m) => "\\" + m);
  if (!uname) return null;
  const { data: member } = await supabase
    .from("members")
    .select("*")
    .ilike("discord_username", uname)
    .eq("active", true)
    .maybeSingle();
  return member ?? null;
}

// deno-lint-ignore no-explicit-any
function publicMember(m: any) {
  const { access_code_hash: _hash, ...rest } = m;
  return rest;
}

// deno-lint-ignore no-explicit-any
async function getBoard(member: any): Promise<Response> {
  const { data: members, error: mErr } = await supabase
    .from("members")
    .select("id, discord_username, display_name, timezone, schedule, role")
    .eq("active", true)
    .order("created_at");
  const { data: tasks, error: tErr } = await supabase
    .from("tasks")
    .select(
      "id, member_id, title, description, due_date, sort_order, status, proof_image_url, completed_at, created_at",
    )
    .order("sort_order")
    .order("created_at");
  if (mErr || tErr) return json(500, { error: "Could not load the board." });
  return json(200, { me: publicMember(member), members, tasks });
}

// deno-lint-ignore no-explicit-any
async function completeTask(member: any, body: any): Promise<Response> {
  const { task_id, image_base64, content_type } = body;
  if (!task_id || typeof task_id !== "string") {
    return json(400, { error: "Missing task." });
  }
  if (!image_base64 || typeof image_base64 !== "string") {
    return json(400, { error: "A proof picture is required to complete a task." });
  }
  const ct = String(content_type || "").toLowerCase();
  const ext = EXT_BY_TYPE[ct];
  if (!ext) {
    return json(400, { error: "Picture must be a JPEG, PNG, or WebP." });
  }
  let bytes: Uint8Array;
  try {
    const bin = atob(image_base64);
    bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  } catch {
    return json(400, { error: "Could not read the picture upload." });
  }
  if (bytes.length > MAX_IMAGE_BYTES) {
    return json(400, { error: "Picture too big (max 4 MB). Crop or retake it." });
  }
  if (bytes.length === 0) {
    return json(400, { error: "A proof picture is required to complete a task." });
  }

  const { data: task } = await supabase
    .from("tasks")
    .select("*")
    .eq("id", task_id)
    .maybeSingle();
  if (!task || task.member_id !== member.id) {
    return json(404, { error: "Task not found." });
  }
  if (task.status === "done") {
    return json(400, { error: "Task is already completed." });
  }

  const path = `${task_id}/${crypto.randomUUID()}.${ext}`;
  const upload = await supabase.storage
    .from("proofs")
    .upload(path, bytes, { contentType: ct });
  if (upload.error) {
    console.error("storage upload failed:", upload.error);
    return json(500, { error: "Upload failed. Try again." });
  }
  const { data: pub } = supabase.storage.from("proofs").getPublicUrl(path);

  // status='open' guard makes double-completion a no-op even under a race.
  const { data: updated } = await supabase
    .from("tasks")
    .update({
      status: "done",
      proof_image_path: path,
      proof_image_url: pub.publicUrl,
      completed_at: new Date().toISOString(),
    })
    .eq("id", task_id)
    .eq("status", "open")
    .select()
    .maybeSingle();
  if (!updated) {
    await supabase.storage.from("proofs").remove([path]);
    return json(400, { error: "Task is already completed." });
  }

  const pinged = await sendDiscordPing(updated, member);
  if (pinged) {
    await supabase
      .from("tasks")
      .update({ ping_sent_at: new Date().toISOString() })
      .eq("id", task_id);
  }
  return json(200, { ok: true, ping_sent: pinged });
}

// Members maintain their own display name, timezone, and weekly schedule.
// Identity (discord_username) and role stay admin-only, and tasks are untouchable
// here - the only task write a member has is complete_task with proof.
// deno-lint-ignore no-explicit-any
async function updateProfile(member: any, body: any): Promise<Response> {
  const fields: Record<string, unknown> = {};
  if ("display_name" in body) {
    fields.display_name = String(body.display_name || "").trim() || null;
  }
  if ("timezone" in body) {
    const tz = String(body.timezone || "");
    if (!validTimezone(tz)) return json(400, { error: "Unknown timezone." });
    fields.timezone = tz;
  }
  if ("schedule" in body) {
    const raw = body.schedule && typeof body.schedule === "object" ? body.schedule : {};
    const schedule: Record<string, string> = {};
    for (const d of DAYS) {
      const v = String(raw[d] ?? "").trim().slice(0, 120);
      if (v) schedule[d] = v;
    }
    fields.schedule = schedule;
  }
  if (Object.keys(fields).length === 0) {
    return json(400, { error: "Nothing to update." });
  }
  const { data: updated, error } = await supabase
    .from("members")
    .update(fields)
    .eq("id", member.id)
    .select("*")
    .maybeSingle();
  if (error || !updated) {
    console.error("update_profile failed:", error);
    return json(500, { error: "Could not save your profile." });
  }
  return json(200, { me: publicMember(updated) });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json(405, { error: "POST only." });
  try {
    let body;
    try {
      body = await req.json();
    } catch {
      return json(400, { error: "Bad request." });
    }
    const member = await authMember(body.username);
    if (!member) {
      return json(401, { error: "Username not on the board. Ask Chris to add you." });
    }
    switch (body.action) {
      case "get_board":
        return await getBoard(member);
      case "complete_task":
        return await completeTask(member, body);
      case "update_profile":
        return await updateProfile(member, body);
      default:
        return json(400, { error: "Unknown action." });
    }
  } catch (err) {
    console.error("member function error:", err);
    return json(500, { error: "Something went wrong. Try again." });
  }
});
