# Cookies setup: authenticated YouTube + Instagram for yt-dlp

One file unlocks full-access research and playback. Every yt-dlp path in this repo reads it:
`watch_batch.py` (download + transcribe), `zoe_music.py`, and the Discord bot's `audio.py`.

Why it is needed:
- YouTube throws "Sign in to confirm you're not a bot" and blocks age/region-gated videos without a session.
- Instagram needs a login cookie for anything past a public teaser.
- On Windows, Chrome/Edge app-bound encryption hides the cookie, so `--cookies-from-browser` fails.
  The reliable path is an exported `cookies.txt`.

## One-time export

1. Install the **Get cookies.txt LOCALLY** browser extension (Chrome or Edge).
   Firefox also works and has no app-bound encryption.
2. Log in to the site in that browser:
   - YouTube: open youtube.com signed in to the account you want.
   - Instagram: open instagram.com signed in.
3. Click the extension, **Export** the cookies for that site as `cookies.txt`.
4. If you use both YouTube and Instagram, export while logged in to both so one file carries both,
   or export each and merge (the extension can export "all sites").

## Where to put it

Pick one, in priority order:

1. Drop the file at `secrets/cookies.txt` in this repo. Nothing else to set.
   (`secrets/` is gitignored, so it never gets committed.)
2. Or set an env var to any path:
   - PowerShell: `setx YTDLP_COOKIES "C:\path\to\cookies.txt"`
   - or add `YTDLP_COOKIES=C:\path\to\cookies.txt` to `.env`
3. `COOKIES=...` still works too (older `watch_batch` convention).

Resolution order across the whole repo: `YTDLP_COOKIES` → `COOKIES` → `secrets/cookies.txt`.

## Verify it works

```
python tools/ytdlp_cookies.py
```
Prints the resolved path, or "(no cookies file found)". Then a real pull, on your machine:
```
python -c "import asyncio,audio; print(asyncio.run(audio.fetch_tracks('https://youtu.be/jNQXAC9IVRw'))[0].title)"
```
Title printed = authenticated pipeline green.

## Rules

- Never commit the cookie file. It is a live login. `.gitignore` blocks `secrets/`, `cookies.txt`,
  and `*.cookies.txt`, but do not paste its contents anywhere either.
- Cookies expire. If pulls start failing with auth errors again, re-export.
- This is a workaround for platform gating, not a sign yt-dlp is broken.
