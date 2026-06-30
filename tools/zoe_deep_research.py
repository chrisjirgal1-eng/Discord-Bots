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
                os.environ.setdefault(k.strip(), v.strip())


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


def research(question, n=6):
    """Search the web and synthesize a cited answer. Returns {ok, answer, sources, live}."""
    load_env()
    q = (question or "").strip()
    if not q:
        return {"ok": False, "error": "no question"}
    sources = _ddg(q, n)
    try:
        if sources:
            src_text = "\n".join(f"[{i+1}] {s['title']} -- {s['url']}\n{s['snippet']}"
                                 for i, s in enumerate(sources))
            ans = _openai([
                {"role": "system", "content": "You are Zoe's research engine for Chris. Answer using "
                 "ONLY the numbered sources. Be concrete and honest; if the sources do not cover it, "
                 "say so. Cite claims inline with [n]. End with a one-line bottom line. Plain "
                 "spoken-friendly prose, no markdown headers."},
                {"role": "user", "content": f"QUESTION: {q}\n\nSOURCES:\n{src_text}"}], max_tokens=700)
            return {"ok": True, "answer": ans, "sources": sources, "live": True}
        ans = _openai([
            {"role": "system", "content": "You are Zoe researching for Chris. Live web search was "
             "unavailable, so answer from your own knowledge and say so up front in one short clause."},
            {"role": "user", "content": q}], max_tokens=600)
        return {"ok": True, "answer": ans, "sources": [], "live": False}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


if __name__ == "__main__":
    import pprint
    pprint.pprint(research(" ".join(sys.argv[1:]) or "best evidence-based protein intake for muscle gain"))
