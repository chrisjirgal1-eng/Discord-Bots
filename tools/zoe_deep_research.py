#!/usr/bin/env python3
"""Zoe's deep-research: live web search + synthesis WITH citations.

No extra API key: DuckDuckGo HTML for sources, OpenAI for synthesis (the key already in .env).
Inspired by OpenJarvis deep_research. Best-effort and never raises; if live search is unavailable
it falls back to a model answer that says so up front, so the tool always returns something useful.

  python tools/zoe_deep_research.py "best evidence-based protein intake for muscle gain"
"""
import os, sys, re, json, html, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")


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


def _ddg(query, n=6):
    """DuckDuckGo HTML results -> [{title, url, snippet}]. Best-effort; [] on failure."""
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception:
        return []
    out = []
    for m in re.finditer(r'result__a[^>]*href="(.*?)".*?>(.*?)</a>', page, re.S):
        href, title = m.group(1), re.sub(r"<.*?>", "", m.group(2))
        href, title = html.unescape(href), html.unescape(title).strip()
        mm = re.search(r"uddg=([^&]+)", href)          # DDG wraps the real url in uddg=
        if mm:
            href = urllib.parse.unquote(mm.group(1))
        if href.startswith("http") and title:
            out.append({"title": title[:120], "url": href, "snippet": ""})
        if len(out) >= n:
            break
    snips = [re.sub(r"<.*?>", "", s) for s in re.findall(r'result__snippet[^>]*>(.*?)</a>', page, re.S)]
    for i, s in enumerate(snips[:len(out)]):
        out[i]["snippet"] = html.unescape(s).strip()[:300]
    return out


def _openai(messages, max_tokens=700):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return ""
    body = json.dumps({"model": os.environ.get("ZOE_RESEARCH_MODEL", "gpt-4o"),
                       "messages": messages, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"].strip()


def _local(query, n=4):
    """Best-effort hits from Chris's own research vault (the semantic reel index). [] on any failure."""
    try:
        import zoe_research
        r = zoe_research.search(query)
        if isinstance(r, list):
            return [{"title": str(x.get("title", "")), "path": str(x.get("path", ""))}
                    for x in r[:n] if isinstance(x, dict)]
    except Exception:
        pass
    return []


def research(question, n=6):
    """Search the web AND Chris's own research vault, then synthesize a cited answer.
    Returns {ok, answer, sources, vault, live}."""
    load_env()
    q = (question or "").strip()
    if not q:
        return {"ok": False, "error": "no question"}
    sources = _ddg(q, n)
    vault = _local(q)
    try:
        if sources or vault:
            parts = [f"[{i+1}] {s['title']} -- {s['url']}\n{s['snippet']}" for i, s in enumerate(sources)]
            parts += [f"[V{j+1}] (Chris's own research vault) {v['title']} -- {v['path']}"
                      for j, v in enumerate(vault)]
            ans = _openai([
                {"role": "system", "content": "You are Zoe's research engine for Chris. Answer using "
                 "the sources below: web sources are numbered [n], and items from his OWN research "
                 "vault are [Vn] -- weight his own vault highly. Be concrete and honest; if the "
                 "sources do not cover it, say so. Cite claims inline with [n] or [Vn]. End with a "
                 "one-line bottom line. Plain spoken-friendly prose, no markdown headers."},
                {"role": "user", "content": f"QUESTION: {q}\n\nSOURCES:\n" + "\n".join(parts)}],
                max_tokens=700)
            return {"ok": True, "answer": ans, "sources": sources, "vault": vault, "live": bool(sources)}
        ans = _openai([
            {"role": "system", "content": "You are Zoe researching for Chris. Live web search was "
             "unavailable, so answer from your own knowledge and say so up front in one short clause."},
            {"role": "user", "content": q}], max_tokens=600)
        return {"ok": True, "answer": ans, "sources": [], "vault": [], "live": False}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _fetch_text(url):
    """Fetch a page and strip it to readable text (bounded). '' on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            page = r.read().decode("utf-8", "replace")
        page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", page)
        return re.sub(r"\s+", " ", html.unescape(text)).strip()[:8000]
    except Exception:
        return ""


def summarize(target):
    """Summarize a URL (fetched) or a block of text. Returns {ok, summary}."""
    load_env()
    t = (target or "").strip()
    if not t:
        return {"ok": False, "error": "nothing to summarize"}
    body = _fetch_text(t) if t.startswith("http") else t
    if not body:
        return {"ok": False, "error": "could not read that"}
    try:
        ans = _openai([
            {"role": "system", "content": "You are Zoe summarizing for Chris. Give a tight, "
             "spoken-friendly summary: the gist in two to four sentences, then the single most useful "
             "takeaway. No markdown headers."},
            {"role": "user", "content": "Summarize this:\n\n" + body[:8000]}], max_tokens=400)
        return {"ok": True, "summary": ans}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def news(topic="", n=6):
    """Top headlines from Google News RSS (no key). Returns {ok, headlines}."""
    try:
        q = urllib.parse.quote((topic or "").strip())
        url = ("https://news.google.com/rss/search?q=%s&hl=en-US&gl=US&ceid=US:en" % q) if q \
            else "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            xml = r.read().decode("utf-8", "replace")
        titles = re.findall(r"<title>(.*?)</title>", xml, re.S)
        heads = [html.unescape(re.sub(r"<.*?>", "", t)).strip() for t in titles[1:n + 1]]  # [0] is feed name
        heads = [h for h in heads if h]
        return {"ok": bool(heads), "headlines": heads}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


if __name__ == "__main__":
    import pprint
    pprint.pprint(research(" ".join(sys.argv[1:]) or "best evidence-based protein intake for muscle gain"))
