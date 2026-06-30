#!/usr/bin/env python3
"""ZOE's hands on the web: a Playwright-driven browser she can actually operate.

She navigates, reads the page, clicks, types, scrolls, and goes back/forward -- everything you
can do on a site. The realtime model drives it through the browser_* tools (tools/zoe_tools.py)
and perceives each page from the snapshot every action returns (title, url, visible text, and the
interactive elements with labels), so it knows what to click next.

Safety: she confirms before anything irreversible (post, send, buy, delete, submit). That guard
is enforced in her persona -- the tools just do what they are told, so the confirmation lives in
the conversation, which is the posture Chris chose.

Design: Playwright's sync API cannot run inside the asyncio voice loop, so the browser lives on
its own dedicated thread that owns the Playwright instance. Tool calls hand a request to that
thread and wait for the result (thread-safe request/response). A persistent profile under
~/.zoe-browser keeps logins between runs -- log into your accounts once in this window.

Local setup (one time, on the Windows machine):
  pip install playwright
  playwright install chromium      # or it uses your installed Chrome via channel="chrome"
"""
import os, sys, threading, queue

USER_DATA = os.path.join(os.path.expanduser("~"), ".zoe-browser")
_MAX_ELEMENTS = 40
_MAX_TEXT = 1200

# Labels that mean money or something you can't take back. Clicking/submitting these is refused
# unless confirmed=true is passed (the model confirms with him verbally first). A backstop to the
# persona guard, so a hallucinated turn can't click "Pay" on its own.
_DANGER = ("buy", "place order", "pay", "purchase", "checkout", "delete", "remove", "send",
           "post", "publish", "tweet", "submit payment", "confirm order", "confirm purchase",
           "unfollow", "unsubscribe")

# JS that returns the clickable/typable elements on the page, each with a short label so the
# model can refer to them by what they say.
_ELEMENTS_JS = """
() => Array.from(document.querySelectorAll(
    'a,button,input,textarea,select,[role=button],[role=link],[role=tab]'))
  .filter(e => e.offsetParent !== null)
  .slice(0, %d)
  .map(e => {
    const label = (e.innerText || e.value || e.getAttribute('aria-label')
                   || e.placeholder || e.name || '').trim().replace(/\\s+/g,' ').slice(0, 60);
    return {tag: e.tagName.toLowerCase(), type: (e.type||''), label};
  })
  .filter(e => e.label);
""" % _MAX_ELEMENTS


class _Browser:
    def __init__(self):
        self._req = queue.Queue()
        self._thread = None
        self._lock = threading.Lock()

    # public, thread-safe: send one command to the browser thread and wait for the result
    def call(self, method, timeout=60, **kwargs):
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, daemon=True)
                self._thread.start()
        done = threading.Event()
        box = {}
        self._req.put((method, kwargs, done, box))
        if not done.wait(timeout=timeout):
            return {"ok": False, "error": "browser timed out"}
        return box.get("result", {"ok": False, "error": "no result"})

    def _run(self):
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            self._drain_error(f"playwright not installed ({e}); run: pip install playwright")
            return
        headless = os.environ.get("ZOE_BROWSER_HEADLESS", "").lower() in ("1", "true", "yes")
        try:
            with sync_playwright() as p:
                ctx = self._launch(p, headless)
                if not ctx.pages:
                    ctx.new_page()
                while True:
                    method, kwargs, done, box = self._req.get()
                    if method == "_shutdown":
                        box["result"] = {"ok": True}; done.set(); break
                    try:
                        box["result"] = self._handle(ctx, method, kwargs)
                    except Exception as e:
                        box["result"] = {"ok": False, "error": str(e)[:200]}
                    done.set()
                try: ctx.close()
                except Exception: pass
        except Exception as e:
            self._drain_error(f"browser failed to start: {str(e)[:200]}")

    def _launch(self, p, headless):
        # an explicit binary wins (ZOE_BROWSER_EXECUTABLE); else his installed Chrome
        # (channel="chrome", his look + codecs); else Playwright's bundled chromium.
        exe = os.environ.get("ZOE_BROWSER_EXECUTABLE")
        if exe:
            return p.chromium.launch_persistent_context(USER_DATA, headless=headless,
                                                        executable_path=exe)
        try:
            return p.chromium.launch_persistent_context(USER_DATA, headless=headless,
                                                        channel="chrome")
        except Exception:
            return p.chromium.launch_persistent_context(USER_DATA, headless=headless)

    def _drain_error(self, msg):
        # answer every pending request with the error, until the queue stays empty briefly,
        # so a request that landed during launch failure never waits out its full timeout
        while True:
            try:
                method, kwargs, done, box = self._req.get(timeout=0.5)
            except queue.Empty:
                return
            box["result"] = {"ok": False, "error": msg}
            done.set()

    def _active(self, ctx):
        """The frontmost live tab. A click can open a popup/new tab; act on and snapshot that
        one, not the stale original, so she is never blind to where she actually landed."""
        pages = [pg for pg in ctx.pages if not pg.is_closed()]
        return pages[-1] if pages else ctx.new_page()

    def _settle(self, page):
        try: page.wait_for_load_state("domcontentloaded", timeout=6000)
        except Exception: pass
        try: page.wait_for_timeout(300)
        except Exception: pass

    # ---- the actual page actions; each returns a fresh snapshot so she can see the result ----
    def _handle(self, ctx, method, kw):
        page = self._active(ctx)
        if method == "open" or method == "goto":
            url = kw.get("url", "")
            if url and "://" not in url and not url.startswith("data:"):
                url = "https://" + url
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        elif method == "click":
            self._click(page, kw.get("text", ""), kw.get("confirmed", False))
            self._settle(page)                 # a click may navigate; wait before snapshotting
        elif method == "type":
            self._type(page, kw.get("field", ""), kw.get("text", ""),
                       kw.get("submit", False), kw.get("confirmed", False))
            self._settle(page)
        elif method == "back":
            page.go_back(wait_until="domcontentloaded")
        elif method == "forward":
            page.go_forward(wait_until="domcontentloaded")
        elif method == "scroll":
            dy = -800 if kw.get("direction", "down") == "up" else 800
            page.mouse.wheel(0, dy)
        elif method == "read":
            pass
        else:
            return {"ok": False, "error": f"unknown browser action {method}"}
        return {"ok": True, **self._snapshot(self._active(ctx))}   # re-resolve: a popup may be up

    def _click(self, page, text, confirmed=False):
        if not text:
            raise ValueError("nothing to click")
        if not confirmed and any(d in text.lower() for d in _DANGER):
            raise ValueError(f"'{text}' looks irreversible -- confirm with him (yes/no), then "
                             "call again with confirmed true")
        try:
            page.get_by_text(text, exact=False).first.click(timeout=5000)
            return
        except Exception:
            pass
        for role in ("button", "link", "tab"):
            try:
                page.get_by_role(role, name=text).first.click(timeout=3000)
                return
            except Exception:
                continue
        page.click(f"text={text}", timeout=4000)   # last resort, raises if not found

    def _type(self, page, field, text, submit, confirmed=False):
        if submit and not confirmed:
            raise ValueError("submitting can be irreversible -- confirm with him (yes/no), then "
                             "call again with submit and confirmed true")
        loc = None
        for finder in (lambda: page.get_by_label(field, exact=False),
                       lambda: page.get_by_placeholder(field, exact=False),
                       lambda: page.locator(f"[name='{field}']")):
            try:
                cand = finder()
                cand.first.wait_for(timeout=2500)
                loc = cand.first
                break
            except Exception:
                continue
        if loc is None:                            # fail rather than guess the wrong field
            raise ValueError(f"no field matching '{field}'")
        loc.fill(text)
        if submit:
            loc.press("Enter")

    def _snapshot(self, page):
        try: title = page.title()
        except Exception: title = ""
        url = page.url
        try: elements = page.evaluate(_ELEMENTS_JS)
        except Exception: elements = []
        try: text = (page.inner_text("body") or "")[:_MAX_TEXT]
        except Exception: text = ""
        return {"title": title, "url": url, "elements": elements, "text": text}


_BROWSER = _Browser()

def action(method, **kwargs):
    """Run one browser action and return a result dict with a page snapshot. Never raises."""
    try:
        return _BROWSER.call(method, **kwargs)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _selftest():
    """Cloud-safe smoke test: drive a real (headless) browser to a page and read it back."""
    os.environ.setdefault("ZOE_BROWSER_HEADLESS", "1")
    r = action("open", url="https://example.com")
    print("open ->", {k: r.get(k) for k in ("ok", "title", "url")})
    assert r.get("ok"), r
    assert "example" in (r.get("title", "").lower() + r.get("url", ""))
    r2 = action("read")
    print("read ->", "ok" if r2.get("ok") else r2, "| elements:", len(r2.get("elements", [])))
    assert r2.get("ok")
    print("browser selftest ok")


if __name__ == "__main__":
    _selftest()
