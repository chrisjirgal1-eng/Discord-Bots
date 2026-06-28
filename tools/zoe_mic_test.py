#!/usr/bin/env python3
"""Zoe mic check + calibration -- make sure Zoe can actually hear you.

  python tools/zoe_mic_test.py          live mic meter: speak and watch your level vs the wake line
  python tools/zoe_mic_test.py --wake   full test: say "hey zoe", see the transcript + if it triggers

If your speaking level does not cross the wake line, Zoe will not hear you. Lower the threshold:
set ZOE_MIC_THRESHOLD in .env to about the value this tool suggests. (Zoe also auto-calibrates to
your room at startup, so usually it just works.)
"""
import os, sys, time, queue
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _bar(rms, thr, width=46, scale=3000.0):
    mark = int(min(rms, scale) / scale * width)
    tpos = min(int(min(thr, scale) / scale * width), width - 1)
    cells = ["#" if i < mark else " " for i in range(width)]
    cells[tpos] = "|"
    return "".join(cells)

def meter(seconds=20):
    import sounddevice as sd, numpy as np
    SR = 16000
    thr = int(os.environ.get("ZOE_MIC_THRESHOLD", "600"))
    dev = sd.query_devices(kind="input")
    print(f"\n  Input device : {dev['name']}")
    print(f"  Wake line    : {thr}   (the | in the bar; ZOE_MIC_THRESHOLD overrides)")
    print("  Speak normally for a few seconds. Your voice must push past the | to wake Zoe.\n")
    q = queue.Queue()
    peak = 0.0
    with sd.InputStream(samplerate=SR, channels=1, dtype="int16",
                        blocksize=1600, callback=lambda i, n, t, s: q.put(i.copy())):
        start = time.time()
        while time.time() - start < seconds:
            try:
                block = q.get(timeout=1)
            except queue.Empty:
                continue
            rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))
            peak = max(peak, rms)
            over = "  <-- loud enough" if rms > thr else ""
            sys.stdout.write(f"\r  [{_bar(rms, thr)}] {int(rms):5d}{over}      ")
            sys.stdout.flush()
    print("\n")
    if peak <= 0:
        print("  No audio captured. Check the mic is plugged in and allowed in Windows mic settings.\n")
        return
    rec = max(int(peak * 0.35), 200)
    print(f"  Your loudest : {int(peak)}")
    if peak > thr:
        print(f"  Good -- your voice clears the wake line ({thr}); Zoe should hear you.")
    else:
        print(f"  Too quiet for the current line ({thr}) -- that is why she misses you.")
    print(f"  Suggested ZOE_MIC_THRESHOLD: {rec}   (put this in your .env)\n")

def wake_test():
    import zoe_assistant as za
    za.load_env()
    dg = os.environ.get("DEEPGRAM_API_KEY")
    if not dg:
        print("  DEEPGRAM_API_KEY missing in .env"); return
    za.RMS_THRESHOLD = za.calibrate_threshold()
    print(f"\n  Wake threshold (auto/env): {za.RMS_THRESHOLD}")
    print('  Say "hey zoe" now ...')
    audio = za.listen_utterance(max_wait=8)
    if audio is None:
        print("  Heard nothing above the threshold -- run the meter and lower ZOE_MIC_THRESHOLD.\n")
        return
    try:
        text = za.stt(za.to_wav(audio), dg)
    except Exception as e:
        print("  transcription error:", e); return
    print(f"  Heard: {text!r}")
    if any(w in text.lower() for w in za.WAKE_WORDS):
        print("  WAKE DETECTED -- Zoe would open now.\n")
    else:
        print("  No wake word in that. Say it clearly, or it was misheard.\n")

if __name__ == "__main__":
    try:
        from jarvis_speak import load_env
        load_env()
    except Exception:
        pass
    try:
        wake_test() if "--wake" in sys.argv else meter()
    except Exception as e:
        print("\n  mic test error:", e)
