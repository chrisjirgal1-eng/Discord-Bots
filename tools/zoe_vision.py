#!/usr/bin/env python3
"""Zoe vision: answer a question about an image with OpenAI vision (the key the voice runs on).

  python tools/zoe_vision.py <image_path> "<question>"

Prints one JSON line: {"ok": true, "answer": "..."} or {"ok": false, "error": "..."}.
Used by the command bar's image upload (electron/main.js -> command:image).
"""
import os, sys, json, base64, mimetypes, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                # .env is authoritative for secrets, so a stale env var can never shadow a real
                # key (the wake-word 401 bug). Config vars keep setdefault so intended overrides win.
                if k.endswith(("_KEY", "_TOKEN", "_VOICE_ID", "_SECRET")):
                    os.environ[k] = v
                else:
                    os.environ.setdefault(k, v)


def answer(image_path, question):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return {"ok": False, "error": "no OPENAI_API_KEY in .env"}
    if not image_path or not os.path.isfile(image_path):
        return {"ok": False, "error": "image not found: " + str(image_path)}
    mime = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as f:
        data_url = f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    model = os.environ.get("ZOE_VISION_MODEL", "gpt-4o")
    body = json.dumps({"model": model, "max_tokens": 700, "messages": [
        {"role": "system", "content":
            "You are Zoe, Chris's AI right hand. Look at the image and answer his question directly "
            "and concisely, like a sharp teammate. Address him as sir or Chris. If he gave no "
            "question, say what the image is and what matters about it."},
        {"role": "user", "content": [
            {"type": "text", "text": question or "What is this? Tell me what matters."},
            {"type": "image_url", "image_url": {"url": data_url}}]}]}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "User-Agent": "curl/8.19.0"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.load(r)
        return {"ok": True, "answer": d["choices"][0]["message"]["content"].strip()}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"OpenAI {e.code}: " + e.read().decode("utf-8", "replace")[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


if __name__ == "__main__":
    load_env()
    img = sys.argv[1] if len(sys.argv) > 1 else ""
    q = " ".join(sys.argv[2:]).strip()
    print(json.dumps(answer(img, q)))
