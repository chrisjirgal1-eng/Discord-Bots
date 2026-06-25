/**
 * ClearCoat Co. — Google Apps Script Backend
 * ============================================
 * SETUP (one-time, takes ~3 minutes):
 *
 * 1. Go to https://sheets.google.com and create a new blank spreadsheet
 * 2. Name it "ClearCoat Co. Tracker"
 * 3. Create 3 tabs at the bottom: "Reviews", "Jobs", "Stats"
 * 4. Copy your Spreadsheet ID from the URL:
 *      https://docs.google.com/spreadsheets/d/  -->COPY THIS PART<--  /edit
 *    Paste it below as SHEET_ID
 * 5. In the spreadsheet, click Extensions → Apps Script
 * 6. Delete everything in the editor and paste this entire file
 * 7. Click Save (floppy disk icon)
 * 8. Click Deploy → New deployment
 *    - Type: Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 9. Click Deploy → copy the Web App URL
 * 10. Paste that URL in index.html where it says:
 *       const SCRIPT_URL = 'YOUR_SCRIPT_URL_HERE';
 *
 * Done! The website will now read/write live data from your Google Sheet.
 */

const SHEET_ID = 'YOUR_SHEET_ID_HERE'; // ← paste your spreadsheet ID here

// ── Shared helpers ────────────────────────────────────────────────────────────

/**
 * Open a named sheet tab, creating the header row if the sheet is empty.
 */
function getSheet(tabName, headers) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const sheet = ss.getSheetByName(tabName);
  if (sheet.getLastRow() === 0 && headers) {
    sheet.appendRow(headers);
  }
  return sheet;
}

/**
 * Read all data rows (excluding the header) from a sheet.
 */
function getDataRows(sheet, numCols) {
  if (sheet.getLastRow() <= 1) return [];
  return sheet.getRange(2, 1, sheet.getLastRow() - 1, numCols).getValues();
}

// ── Entry point for all requests ──────────────────────────────────────────────

function doGet(e) {
  const action = e.parameter.action || 'get_data';
  let result;

  try {
    if (action === 'submit_review') {
      result = submitReview(e.parameter);
    } else if (action === 'log_job') {
      result = logJob(e.parameter);
    } else {
      result = getData();
    }
  } catch (err) {
    result = { success: false, error: err.message };
  }

  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// ── Get live stats + reviews ──────────────────────────────────────────────────

function getData() {
  const rSheet = getSheet('Reviews', ['Date', 'Name', 'Service', 'Stars', 'Review', 'Approved']);
  const rData  = getDataRows(rSheet, 6);

  const reviews = rData
    .filter(r => r[0] && r[5] !== false) // has date + approved
    .map(r => ({
      date:    Utilities.formatDate(new Date(r[0]), Session.getScriptTimeZone(), 'MMM d, yyyy'),
      name:    r[1],
      service: r[2],
      stars:   r[3],
      text:    r[4],
    }))
    .reverse() // newest first
    .slice(0, 6);

  const avgRating = rData.length
    ? (rData.reduce((s, r) => s + (r[3] || 0), 0) / rData.length).toFixed(1)
    : '5.0';

  const jSheet     = getSheet('Jobs', ['Date', 'Service', 'Amount', 'Notes']);
  const jData      = getDataRows(jSheet, 4);
  const totalJobs    = jData.filter(r => r[0]).length;
  const totalRevenue = jData.reduce((s, r) => s + (Number(r[2]) || 0), 0);

  return {
    success: true,
    stats: { totalJobs, totalRevenue, avgRating, reviewCount: rData.length },
    reviews,
  };
}

// ── Submit a review ───────────────────────────────────────────────────────────

function submitReview(p) {
  if (!p.name || !p.text || !p.stars) throw new Error('Missing fields');

  const sheet = getSheet('Reviews', ['Date', 'Name', 'Service', 'Stars', 'Review', 'Approved']);
  sheet.appendRow([new Date(), p.name, p.service || '', Number(p.stars), p.text, true]);
  return { success: true };
}

// ── Log a completed job ───────────────────────────────────────────────────────

function logJob(p) {
  if (!p.service || !p.amount) throw new Error('Missing service or amount');

  const sheet = getSheet('Jobs', ['Date', 'Service', 'Amount', 'Notes']);
  sheet.appendRow([new Date(), p.service, Number(p.amount), p.notes || '']);
  return { success: true };
}
