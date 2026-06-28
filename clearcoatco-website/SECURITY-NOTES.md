# Clearcoat site: security findings

Audit 2026-06-27 (autonomous build run). Scope: `google-apps-script.js` (deployed as a public
"Anyone" web app) and `index.html`. These touch the live business site, so they are flagged for
Chris to apply on his next deploy, not changed automatically. Ranked by real impact.

## 1. High: anyone can write fake jobs, and the admin password is client-side

- The web app is deployed with access "Anyone", and `doGet` routes `action=log_job` straight to
  `logJob`, which appends to the Jobs sheet. Nothing server-side checks who is calling.
- The only gate is `ADMIN_PASS` in `index.html` (around line 964), which is visible to anyone who
  views page source, and the Apps Script never checks it. So anyone can call
  `SCRIPT_URL?action=log_job&service=X&amount=999999` and inflate the public "Revenue Earned" and
  "Jobs Completed" stats.
- Fix (pick one):
  - Add a server-side shared secret: a constant `JOB_TOKEN` in the Apps Script, and make `logJob`
    reject calls where `p.token !== JOB_TOKEN`. Send the token from the admin form. This stops
    drive-by URL abuse. (The token still ships in the page, so treat it as low, not real, auth.)
  - Better: drop `log_job` from the public endpoint and log jobs directly in the Google Sheet, or
    behind a Google-account-gated Apps Script. Removes the public write path entirely.

## 2. Medium: reviews auto-publish, and spam poisons the stats even if you moderate

Two linked problems, both from the public endpoint plus unfiltered aggregation:

- Auto-publish: `submitReview` appends the row with Approved = `true`, so a submitted review shows
  immediately. Worse, the display filter is `r[5] !== false` (gas line 81), which also passes rows
  whose Approved cell is BLANK (`"" !== false` is true). So the "Approved" column does nothing
  unless a cell is explicitly set to `false`. Anyone can post a fake or malicious review and it
  appears live.
- Stat poisoning: `avgRating` and `reviewCount` (gas lines 92-104) are computed over the raw,
  unfiltered `rData`, not the filtered display list. So even after you add display moderation,
  100 one-star spam submissions tank the shown average rating and review count instantly.
- Not an XSS hole: `index.html` escapes review text, name, service, and date with `escapeHTML` in
  `renderReviewCard`, and the server `sanitize()` strips tags. The issue is unmoderated public
  content and stat math, not injection.
- Fix: in `submitReview`, append Approved = `false` (pending). Change the display filter to require
  `r[5] === true`. Compute `avgRating` and `reviewCount` over only the approved rows, not all rows.
  Update the success copy in `index.html` from "It's been posted" to "It'll show after a quick review."

## 3. Low: state changes happen over GET

- `submit_review` and `log_job` mutate data through `doGet`. GET should be safe and idempotent;
  writing on GET invites accidental triggers by crawlers or link prefetchers and CSRF-style abuse.
- Fix: move writes to `doPost` and have the frontend POST. Larger change, lower urgency than 1 and 2.

## 4. Low: raw error messages returned to the client

- `doGet` returns `{ success: false, error: err.message }`. That can leak internal details.
- Fix: log the real error server-side, return a generic message to the client.

## Already solid (no change needed)

- Review rendering escapes HTML on the client, so submitted text cannot inject markup or scripts.
- Server-side `sanitize()` strips tags and caps length on every written field.
- Revenue is shown on purpose (the "Revenue Earned" stat), so returning it from `getData` is fine.

## Bot and Python

Separately reviewed during the Devin merge and covered by the 53-test suite. No new findings here.
