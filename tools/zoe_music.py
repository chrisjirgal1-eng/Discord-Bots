#!/usr/bin/env python3
"""Background music for ZOE: loop a track, ducked under her voice, until told to stop.

Decodes any audio file (mp3, m4a, wav) with the bundled ffmpeg into raw PCM and streams it
through sounddevice on a daemon thread at a low gain so her voice sits on top. start() begins
the loop, stop() ends it. Used for cinematic moments like the capabilities rundown.

Set ZOE_MUSIC in .env to your track (Avengers-style score, your own file -- not shipped here),
or pass a path to start(). ZOE_MUSIC_GAIN (default 0.25) sets how loud the music sits under her.
"""
import os, sys, threading, subprocess

SR = 24000                      # match her voice stream (pcm16 mono 24k)
_thread = None
_stop = threading.Event()


def _resolve(track):
    if track:
        t = os.path.expanduser(os.path.expandvars(str(track).strip().strip('"')))
        if os.path.exists(t):
            return t
    env = os.environ.get("ZOE_MUSIC")
    if env:
        env = os.path.expanduser(os.path.expandvars(env))
        if os.path.exists(env):
            return env
    return None


def _gain():
    try:
        return float(os.environ.get("ZOE_MUSIC_GAIN", "0.25"))
    except ValueError:
        return 0.25


def _loop(path, gain):
    import imageio_ffmpeg, sounddevice as sd, numpy as np
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = sd.RawOutputStream(samplerate=SR, channels=1, dtype="int16")
    out.start()
    try:
        while not _stop.is_set():
            proc = subprocess.Popen(
                [ff, "-loglevel", "quiet", "-i", path, "-f", "s16le", "-ac", "1",
                 "-ar", str(SR), "pipe:1"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            leftover = b""
            try:
                while not _stop.is_set():
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        break                       # track ended -> loop restarts it
                    data = leftover + chunk
                    n = len(data) - (len(data) % 2)  # whole 16-bit frames only
                    frame, leftover = data[:n], data[n:]
                    if not frame:
                        continue
                    if gain != 1.0:
                        a = np.frombuffer(frame, dtype="<i2").astype(np.float32) * gain
                        np.clip(a, -32768, 32767, out=a)
                        frame = a.astype("<i2").tobytes()
                    out.write(frame)
            finally:
                try: proc.kill()
                except Exception: pass
    finally:
        try: out.abort(); out.close()
        except Exception: pass


def start(track="", gain=None):
    """Begin looping the track in the background. Returns a small result dict."""
    stop()
    path = _resolve(track)
    if not path:
        return {"ok": False, "error": "no music file (set ZOE_MUSIC in .env or pass a path)"}
    _stop.clear()
    global _thread
    _thread = threading.Thread(target=_loop, args=(path, _gain() if gain is None else gain),
                               daemon=True)
    _thread.start()
    return {"ok": True, "track": os.path.basename(path)}


def stop():
    """Stop the music if it is playing."""
    _stop.set()
    t = _thread
    if t and t.is_alive():
        t.join(timeout=2)
    return {"ok": True}


def is_playing():
    t = _thread
    return bool(t and t.is_alive() and not _stop.is_set())


if __name__ == "__main__":
    # quick manual test: python tools/zoe_music.py <file>  (Ctrl+C to stop)
    print(start(sys.argv[1] if len(sys.argv) > 1 else ""))
    try:
        import time
        while is_playing():
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop()
