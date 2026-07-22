#!/usr/bin/env python3
"""Windows/Python port of watch-batch.sh: download each video's audio and
transcribe with Groq Whisper. Works without yt-dlp or ffmpeg on PATH (uses the
yt_dlp module and the imageio-ffmpeg bundled binary), and supports a cookies
file for sites that need a login (e.g. Instagram).

Usage:
  python tools/watch_batch.py tools/video-urls.txt transcripts/ [cookies.txt]

GROQ_API_KEY is read from the environment or a local .env file (gitignored).
Cookies file path may also come from YTDLP_COOKIES/COOKIES env or secrets/cookies.txt
(see COOKIES-SETUP.md).
Image /p/ carousel posts have no audio and get marked __FAILED__. That is expected.
"""
import os, re, sys, time, subprocess, urllib.request, json, mimetypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_env():
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def ffmpeg_path():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def vid_id(url, n):
    m = re.search(r"/(reel|p|tv)/([^/?]+)", url)
    return m.group(2) if m else f"video_{n}"

def download_audio(url, base, cookies, ff):
    cmd = [sys.executable, "-m", "yt_dlp", "-q", "--no-warnings",
           "-f", "bestaudio/best", "-x", "--audio-format", "mp3",
           "--ffmpeg-location", ff, "-o", base + ".%(ext)s", url]
    if cookies:
        cmd[3:3] = ["--cookies", cookies]  # after "python -m yt_dlp"
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    return r.returncode == 0, (r.stderr or "").strip().splitlines()[-1:]

def transcribe(audio, key):
    import io
    boundary = "----jarvisformboundary"
    with open(audio, "rb") as f:
        data = f.read()
    parts = []
    def add(name, val):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{val}\r\n".encode())
    add("model", "whisper-large-v3")
    add("response_format", "text")
    parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                  f"filename=\"{os.path.basename(audio)}\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode())
    parts.append(data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/audio/transcriptions", data=body,
        headers={"Authorization": f"Bearer {key}",
                 "User-Agent": "curl/8.19.0",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read().decode("utf-8", "replace")

def main():
    load_env()
    urls_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "video-urls.txt")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "transcripts")
    from ytdlp_cookies import cookies_file
    cookies = sys.argv[3] if len(sys.argv) > 3 else (cookies_file() or "")
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        sys.exit("set GROQ_API_KEY (env or .env)")
    ff = ffmpeg_path()
    os.makedirs(out, exist_ok=True)
    urls = [u.strip() for u in open(urls_file, encoding="utf-8")
            if u.strip() and not u.strip().startswith("#")]
    ok = fail = 0
    for i, url in enumerate(urls, 1):
        vid = vid_id(url, i)
        base = os.path.join(out, vid)
        txt = base + ".txt"
        if os.path.exists(txt) and os.path.getsize(txt) > 0 and not open(txt, encoding="utf-8").read().startswith("__FAILED__"):
            print(f"[{i}/{len(urls)}] {vid} already transcribed, skip"); ok += 1; continue
        print(f"[{i}/{len(urls)}] {vid} downloading audio...", flush=True)
        dl_ok, errtail = download_audio(url, base, cookies, ff)
        audio = base + ".mp3"
        if not dl_ok or not os.path.exists(audio):
            reason = (errtail[0] if errtail else "download")[:120]
            open(txt, "w", encoding="utf-8").write(f"__FAILED__ download: {reason}\n")
            print(f"[{i}/{len(urls)}] {vid} download FAILED: {reason}"); fail += 1; continue
        print(f"[{i}/{len(urls)}] {vid} transcribing (Groq Whisper)...", flush=True)
        try:
            text = transcribe(audio, key)
            open(txt, "w", encoding="utf-8").write(text)
            print(f"[{i}/{len(urls)}] {vid} done ({len(text)} chars)"); ok += 1
        except Exception as e:
            open(txt, "w", encoding="utf-8").write(f"__FAILED__ transcribe: {e}\n")
            print(f"[{i}/{len(urls)}] {vid} transcribe FAILED: {e}"); fail += 1
        finally:
            try: os.remove(audio)
            except OSError: pass
        time.sleep(2)  # polite to Instagram + Groq rate limits
    print(f"\nDone. {ok} ok, {fail} failed, out of {len(urls)}. Transcripts in {out}/")

if __name__ == "__main__":
    main()
