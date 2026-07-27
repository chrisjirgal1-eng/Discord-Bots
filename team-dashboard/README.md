# Zenthra Team Dashboard

Task board for the dev team. Chris assigns tasks per member; members check them off
with a mandatory proof screenshot; every completion pings Chris on Discord with the picture.

## URLs

PRIMARY (Vercel, no personal name in the address - Chris's pick):

- Member board: https://zenthra-dev-team.vercel.app/
- Admin board: https://zenthra-dev-team.vercel.app/admin.html

Backup (GitHub Pages, same site): https://chrisjirgal1-eng.github.io/Discord-Bots/

Backend: Supabase project `zenthra-team-dashboard` (`rmbcnthetpiubiyasipp`),
Edge Functions `admin` + `member`.

### Hosting

- Vercel project `zenthra-dev-team` (Zen Peak Studios team), git-imported from this
  repo with Root Directory `team-dashboard`, framework Other, no build. It redeploys
  automatically on every push to the default branch. Chris created the project by
  importing the repo in the Vercel dashboard (the connector token cannot create
  projects, 403 role denial).
- GitHub Pages stays as a free backup, deployed by
  `.github/workflows/deploy-dashboard-pages.yml` on pushes touching `team-dashboard/`
  (Pages source = "GitHub Actions", set once by Chris in repo settings).
- Supabase cannot serve HTML on its own domain (it rewrites text/html to text/plain
  as an anti-phishing rule); the leftover `site` and `sitepush` Edge Functions are
  inert 410 stubs from discovering that.
- Fallback that always works: pull the repo and open `team-dashboard/admin.html`
  as a local file. The API allows any origin.

## How it works

- Static HTML/JS, no build step. `shared.js` holds the Supabase URL + anon key
  (safe to ship: RLS is deny-all, the key can only invoke the two functions).
- All reads/writes go through the Edge Functions. They run with the service role:
  - `admin`: `x-admin-code` header, sha256-checked against `app_config.admin_code_hash`.
  - `member`: username-only login (Chris's choice for zero friction). Anyone who knows
    the link and an active member's username can open that member's board; the server
    still blocks completing anyone else's task and still requires the proof image.
  - Members self-serve their own profile ("edit profile" next to log out): display
    name, timezone, weekly schedule. Scoped server-side to their own row
    (`update_profile`). Username and role stay admin-only; tasks are untouchable
    from the member side except proof-gated completion.
- Proof images: client compresses to <=1600px JPEG, server enforces type + 4MB cap,
  stored in the public `proofs` bucket under unguessable UUID paths.
- Discord ping: the `member` function POSTs to the webhook in `app_config` after each
  completion (mention + task + member + proof image). Ping failure never blocks the
  completion; the admin board shows a "ping failed" badge with one-click resend.
- Live updates: the admin board polls every 10s (members every 30s) + on tab focus.
- Versioning: `DASH_VERSION` in `shared.js` shows in every tagline and login screen.
  BUMP IT WITH EVERY DASHBOARD CHANGE. Open tabs also watch their own URL's etag
  and reload themselves after a deploy (only when idle: no typing, form, or modal),
  so stale tabs stop resurrecting old bugs.

## One-time setup (the three things only Chris has)

Seed these into `app_config` (via Claude with the Supabase MCP, or the Supabase SQL editor):

```sql
create extension if not exists pgcrypto;
insert into app_config (key, value) values
  ('admin_code_hash', encode(digest('YOUR-ADMIN-PASSCODE', 'sha256'), 'hex')),
  ('discord_webhook_url', 'https://discord.com/api/webhooks/XXXX/YYYY'),
  ('chris_discord_id', 'YOUR-DISCORD-USER-ID')
on conflict (key) do update set value = excluded.value;
```

1. **Discord webhook**: Server Settings > Integrations > Webhooks > New Webhook >
   pick the channel > Copy Webhook URL.
2. **Discord user ID** (for the @ping): Discord Settings > Advanced > Developer Mode ON,
   then right-click your name > Copy User ID.
3. **Admin passcode**: pick one; only its hash is stored.

Until these are seeded, the admin board is locked (deny-by-default) and pings are off.
After seeding, hit "Test Discord ping" on the admin board to prove the webhook live.

## Daily flow

1. Admin board > Add team member (username, timezone, schedule).
2. Add tasks on their card (title, due date, details).
3. They open the member board, type their Discord username once (saved on their
   device), and check off work with a screenshot.
4. You get the Discord ping and watch the board update live.

## Runbook

- **Member leaves**: Edit member > Deactivate (board access off, history kept).
- **Rotate webhook / reset passcode**: rerun the seed SQL above with new values. No redeploy.
- **"Ping failed" badge**: webhook was deleted/rotated or Discord hiccuped. Fix the URL if
  needed, then click "Resend ping" on the task.
- **Site dead / functions 5xx**: the free Supabase project pauses after ~1 week of inactivity.
  Restore it from the Supabase dashboard (or ask Claude: `restore_project`). Normal use
  (anyone opening the board) keeps it awake.
- **Uploads failing on huge images**: client already compresses; server caps at 4 MB.
  If it ever becomes a real limit, switch `complete_task` to a signed-upload-URL two-step
  (create signed URL, client PUTs, then complete referencing the path).

## Code layout

- `team-dashboard/` - `index.html` (member), `admin.html` (Chris), `shared.js`, `style.css`
- `supabase/migrations/20260726000000_team_dashboard_init.sql` - schema, RLS, bucket
- `supabase/functions/admin/index.ts`, `supabase/functions/member/index.ts` - the API
