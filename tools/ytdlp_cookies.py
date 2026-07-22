#!/usr/bin/env python3
"""Resolve a cookies.txt file for yt-dlp, so authenticated YouTube/Instagram pulls work.

One convention for every yt-dlp call site (watch_batch, zoe_music, the Discord bot):
  1. YTDLP_COOKIES env var  (canonical)
  2. COOKIES env var        (back-compat with older watch_batch usage)
  3. <repo>/secrets/cookies.txt  (drop the file, no env var needed)

Returns an existing file path or None. Never returns a path that does not exist, so a call
site can pass the result straight to yt-dlp and simply skip cookies when there are none.
The cookie file stays out of git (see .gitignore); export it per COOKIES-SETUP.md.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cookies_file():
    for var in ("YTDLP_COOKIES", "COOKIES"):
        p = os.environ.get(var)
        if p:
            p = os.path.expanduser(os.path.expandvars(p.strip().strip('"')))
            if os.path.exists(p):
                return p
    default = os.path.join(ROOT, "secrets", "cookies.txt")
    return default if os.path.exists(default) else None


if __name__ == "__main__":
    print(cookies_file() or "(no cookies file found)")
