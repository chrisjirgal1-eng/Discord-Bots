// Shared helpers for the Zenthra team dashboard.
// The anon key is safe to ship: RLS is deny-all, it can only invoke the
// Edge Functions, and those check real credentials server-side.
const SUPABASE_URL = "https://rmbcnthetpiubiyasipp.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJtYmNudGhldHBpdWJpeWFzaXBwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUxMDA0NjcsImV4cCI6MjEwMDY3NjQ2N30.D7ZmX_Gi4Uj8Tk8ciI5tyIzjYhiKCSKYxf2jA4zA_gw";

// Shown on every screen and bumped on every dashboard change, so a glance at
// the tagline tells which code a tab is running.
const DASH_VERSION = "v5";

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

/* Searchable timezone picker. The full IANA list (every country, every
   continent) comes from the browser; IANA ids are city-based, so a small
   country-name alias map makes searches like "india" or "nigeria" land. */

function tzAllZones() {
  return (typeof Intl.supportedValuesOf === "function")
    ? Intl.supportedValuesOf("timeZone")
    : ["America/Chicago", "America/New_York", "America/Denver", "America/Los_Angeles", "Europe/London", "UTC"];
}

const TZ_COUNTRY_ALIASES = {
  "uk": ["Europe/London"], "england": ["Europe/London"], "britain": ["Europe/London"],
  "ireland": ["Europe/Dublin"], "france": ["Europe/Paris"], "germany": ["Europe/Berlin"],
  "spain": ["Europe/Madrid"], "italy": ["Europe/Rome"], "portugal": ["Europe/Lisbon"],
  "netherlands": ["Europe/Amsterdam"], "belgium": ["Europe/Brussels"],
  "sweden": ["Europe/Stockholm"], "norway": ["Europe/Oslo"], "denmark": ["Europe/Copenhagen"],
  "finland": ["Europe/Helsinki"], "poland": ["Europe/Warsaw"], "greece": ["Europe/Athens"],
  "turkey": ["Europe/Istanbul"], "ukraine": ["Europe/Kyiv"], "russia": ["Europe/Moscow"],
  "switzerland": ["Europe/Zurich"], "austria": ["Europe/Vienna"], "czech": ["Europe/Prague"],
  "romania": ["Europe/Bucharest"], "hungary": ["Europe/Budapest"],
  "india": ["Asia/Kolkata"], "pakistan": ["Asia/Karachi"], "bangladesh": ["Asia/Dhaka"],
  "sri lanka": ["Asia/Colombo"], "nepal": ["Asia/Kathmandu"], "china": ["Asia/Shanghai"],
  "japan": ["Asia/Tokyo"], "korea": ["Asia/Seoul"], "south korea": ["Asia/Seoul"],
  "philippines": ["Asia/Manila"], "indonesia": ["Asia/Jakarta"],
  "malaysia": ["Asia/Kuala_Lumpur"], "thailand": ["Asia/Bangkok"],
  "vietnam": ["Asia/Ho_Chi_Minh"], "taiwan": ["Asia/Taipei"],
  "israel": ["Asia/Jerusalem"], "saudi arabia": ["Asia/Riyadh"], "uae": ["Asia/Dubai"],
  "iran": ["Asia/Tehran"], "iraq": ["Asia/Baghdad"], "kazakhstan": ["Asia/Almaty"],
  "egypt": ["Africa/Cairo"], "nigeria": ["Africa/Lagos"], "ghana": ["Africa/Accra"],
  "kenya": ["Africa/Nairobi"], "south africa": ["Africa/Johannesburg"],
  "morocco": ["Africa/Casablanca"], "ethiopia": ["Africa/Addis_Ababa"],
  "tanzania": ["Africa/Dar_es_Salaam"], "algeria": ["Africa/Algiers"],
  "tunisia": ["Africa/Tunis"], "uganda": ["Africa/Kampala"], "zimbabwe": ["Africa/Harare"],
  "usa": ["America/New_York", "America/Chicago", "America/Denver", "America/Phoenix", "America/Los_Angeles", "America/Anchorage", "Pacific/Honolulu"],
  "united states": ["America/New_York", "America/Chicago", "America/Denver", "America/Phoenix", "America/Los_Angeles", "America/Anchorage", "Pacific/Honolulu"],
  "canada": ["America/Toronto", "America/Winnipeg", "America/Edmonton", "America/Vancouver", "America/Halifax"],
  "mexico": ["America/Mexico_City"], "brazil": ["America/Sao_Paulo"],
  "argentina": ["America/Argentina/Buenos_Aires"], "chile": ["America/Santiago"],
  "colombia": ["America/Bogota"], "peru": ["America/Lima"], "venezuela": ["America/Caracas"],
  "ecuador": ["America/Guayaquil"], "bolivia": ["America/La_Paz"],
  "uruguay": ["America/Montevideo"], "paraguay": ["America/Asuncion"],
  "jamaica": ["America/Jamaica"], "cuba": ["America/Havana"],
  "dominican republic": ["America/Santo_Domingo"], "guatemala": ["America/Guatemala"],
  "costa rica": ["America/Costa_Rica"], "panama": ["America/Panama"],
  "honduras": ["America/Tegucigalpa"],
  "australia": ["Australia/Sydney", "Australia/Melbourne", "Australia/Brisbane", "Australia/Adelaide", "Australia/Perth", "Australia/Darwin", "Australia/Hobart"],
  "new zealand": ["Pacific/Auckland"], "fiji": ["Pacific/Fiji"],
};

function tzOffsetLabel(tz) {
  try {
    const parts = new Intl.DateTimeFormat("en-US", { timeZone: tz, timeZoneName: "shortOffset" })
      .formatToParts(new Date());
    const raw = (parts.find((p) => p.type === "timeZoneName") || {}).value || "";
    return raw.replace("GMT", "UTC") || "UTC";
  } catch { return ""; }
}

function tzSearch(query) {
  const zones = tzAllZones();
  const qs = query.trim().toLowerCase();
  if (!qs) return zones;
  const q = qs.replace(/\s+/g, "_");
  const hits = zones.filter((z) => z.toLowerCase().includes(q));
  if (qs.length >= 2) {
    for (const [alias, zs] of Object.entries(TZ_COUNTRY_ALIASES)) {
      if (!alias.startsWith(qs)) continue;
      // No zones.includes() guard: some browsers list legacy spellings
      // (Asia/Calcutta) while the alias targets modern ids (Asia/Kolkata);
      // every alias target is a valid IANA id Intl accepts either way.
      for (const z of zs) {
        if (!hits.includes(z)) hits.unshift(z);
      }
    }
  }
  return hits;
}

// The hidden input keeps the old <select> id, so callers still read
// document.getElementById(id).value for the committed zone.
function tzPickerHtml(id, selected) {
  return `
    <div class="tz-picker" id="${id}-wrap">
      <input type="text" id="${id}-search" value="${escapeHtml(selected)}" autocomplete="off"
             placeholder="Search a city or country, e.g. Tokyo, India">
      <input type="hidden" id="${id}" value="${escapeHtml(selected)}">
      <div class="tz-list" id="${id}-list" hidden></div>
    </div>`;
}

function wireTzPicker(id) {
  const search = document.getElementById(`${id}-search`);
  const hidden = document.getElementById(id);
  const list = document.getElementById(`${id}-list`);
  if (!search || !hidden || !list) return;
  const render = () => {
    const hits = tzSearch(search.value === hidden.value ? "" : search.value);
    const shown = hits.slice(0, 80);
    list.innerHTML = (shown.map((z) =>
      `<div class="tz-opt${z === hidden.value ? " sel" : ""}" data-tz="${escapeHtml(z)}">${escapeHtml(z)} <span>${escapeHtml(tzOffsetLabel(z))}</span></div>`).join("")
      + (hits.length > shown.length ? `<div class="tz-more">${hits.length - shown.length} more - keep typing to narrow it</div>` : ""))
      || `<div class="tz-more">No match - try a big city in that country</div>`;
    list.hidden = false;
  };
  search.addEventListener("focus", () => { search.select(); render(); });
  search.addEventListener("input", render);
  search.addEventListener("blur", () => setTimeout(() => {
    list.hidden = true;
    search.value = hidden.value; // never leave a half-typed non-zone showing
  }, 150));
  list.addEventListener("mousedown", (e) => {
    const opt = e.target.closest("[data-tz]");
    if (!opt) return;
    e.preventDefault(); // keep focus so blur doesn't undo the pick
    hidden.value = opt.dataset.tz;
    search.value = opt.dataset.tz;
    list.hidden = true;
  });
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
