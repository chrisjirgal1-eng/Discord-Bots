// Shared helpers for the Zenthra team dashboard.
// The anon key is safe to ship: RLS is deny-all, it can only invoke the
// Edge Functions, and those check real credentials server-side.
const SUPABASE_URL = "https://rmbcnthetpiubiyasipp.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJtYmNudGhldHBpdWJpeWFzaXBwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUxMDA0NjcsImV4cCI6MjEwMDY3NjQ2N30.D7ZmX_Gi4Uj8Tk8ciI5tyIzjYhiKCSKYxf2jA4zA_gw";

// Shown on every screen and bumped on every dashboard change, so a glance at
// the tagline tells which code a tab is running.
const DASH_VERSION = "v4";

// Boards stay open for days but the HTML only updates on a reload, so a stale
// tab keeps old bugs alive after a deploy. Poll our own URL's etag; when a new
// deploy lands, reload once nothing on screen would be lost.
function watchForNewVersion(intervalMs = 5 * 60 * 1000) {
  let baseline = null;
  const check = async () => {
    let tag = null;
    try {
      const res = await fetch(location.pathname, { method: "HEAD", cache: "no-store" });
      tag = res.headers.get("etag");
    } catch { return; }
    if (!tag) return;               // host without etags: watcher stays quiet
    if (baseline === null) { baseline = tag; return; }
    if (tag === baseline) return;
    const a = document.activeElement;
    if (a && a.matches && a.matches("input, textarea, select")) return;
    if (document.querySelector("#modal-root .modal-overlay")) return;
    if (document.querySelector(".inline-form")) return;
    location.reload();
  };
  check();
  setInterval(check, intervalMs);
  return check;
}

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
const DAY_LABELS = {
  mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu",
  fri: "Fri", sat: "Sat", sun: "Sun",
};

async function api(fn, body, headers = {}) {
  let res;
  try {
    res = await fetch(`${SUPABASE_URL}/functions/v1/${fn}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        ...headers,
      },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error("Can't reach the server. Check your connection and try again.");
  }
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON error body */ }
  if (!res.ok) {
    const msg = (data && data.error) ||
      (res.status >= 500
        ? "The server is waking up or having a moment. Try again in a minute."
        : "Request failed.");
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function timeIn(tz) {
  try {
    return new Intl.DateTimeFormat("en-US", {
      timeZone: tz, hour: "numeric", minute: "2-digit",
    }).format(new Date());
  } catch { return "--:--"; }
}

// Weekday key ("mon".."sun") for right now in the given timezone.
function todayKeyIn(tz) {
  try {
    return new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short" })
      .format(new Date()).toLowerCase().slice(0, 3);
  } catch { return ""; }
}

// "2026-08-01" -> "Fri, Aug 1"
function fmtDue(dateStr) {
  const d = new Date(dateStr + "T12:00:00Z");
  if (isNaN(d)) return dateStr;
  return d.toLocaleDateString("en-US", {
    weekday: "short", month: "short", day: "numeric", timeZone: "UTC",
  });
}

// Is a YYYY-MM-DD due date in the past for someone living in tz?
function isOverdue(dateStr, tz) {
  try {
    const today = new Intl.DateTimeFormat("en-CA", {
      timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit",
    }).format(new Date());
    return dateStr < today;
  } catch { return false; }
}

function timeAgo(iso) {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

function scheduleGridHtml(schedule, tz) {
  const today = todayKeyIn(tz);
  return `<div class="week-grid">` + DAYS.map((d) => `
    <div class="day-cell${d === today ? " today" : ""}">
      <div class="day-name">${DAY_LABELS[d]}</div>
      <div class="day-plan">${escapeHtml((schedule || {})[d] || "-")}</div>
    </div>`).join("") + `</div>`;
}

function tzOptionsHtml(selected) {
  const zones = (typeof Intl.supportedValuesOf === "function")
    ? Intl.supportedValuesOf("timeZone")
    : ["America/Chicago", "America/New_York", "America/Denver", "America/Los_Angeles", "Europe/London", "UTC"];
  return zones.map((z) =>
    `<option value="${escapeHtml(z)}"${z === selected ? " selected" : ""}>${escapeHtml(z)}</option>`).join("");
}

function dayInputsHtml(prefix, schedule = {}) {
  return `<div class="form-days">` + DAYS.map((d) => `
    <div>
      <label>${DAY_LABELS[d]}</label>
      <input type="text" id="${prefix}-${d}" placeholder="-" value="${escapeHtml(schedule[d] || "")}">
    </div>`).join("") + `</div>`;
}

function readSchedule(prefix) {
  const out = {};
  for (const d of DAYS) {
    const v = document.getElementById(`${prefix}-${d}`).value.trim();
    if (v) out[d] = v;
  }
  return out;
}

function progressBarHtml(done, total) {
  const pct = total ? Math.round((done / total) * 100) : 0;
  return `
    <div class="progress-row">
      <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
      <span class="progress-label">${done}/${total} done</span>
    </div>`;
}

function arrayBufferToBase64(buf) {
  const bytes = new Uint8Array(buf);
  let bin = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }
  return btoa(bin);
}

// Recompress a picked image to a <=1600px JPEG so phone screenshots
// upload fast and stay far under the server's 4 MB cap.
async function compressImage(file, maxEdge = 1600, quality = 0.8) {
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    // Browser can't decode it (odd format). Send as-is if it's small enough.
    const okTypes = ["image/jpeg", "image/png", "image/webp"];
    if (okTypes.includes(file.type) && file.size <= 4 * 1024 * 1024) {
      return { base64: arrayBufferToBase64(await file.arrayBuffer()), contentType: file.type };
    }
    throw new Error("Couldn't read that image. Use a JPEG or PNG screenshot.");
  }
  const scale = Math.min(1, maxEdge / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  const blob = await new Promise((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", quality)
  );
  if (!blob) throw new Error("Couldn't process that image. Try a different one.");
  return { base64: arrayBufferToBase64(await blob.arrayBuffer()), contentType: "image/jpeg" };
}
