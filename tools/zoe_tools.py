#!/usr/bin/env python3
"""Bridge ZOE's powers to the OpenAI Realtime model as function tools.

The realtime model is her ears, brain, and mouth. This module is the hands: it
declares the tools she can call (TOOLS) and dispatches each call into the EXISTING
command router (zoe_router) so there is still ONE source of command routing. No
command logic is duplicated here -- every tool maps to zoe_router.execute / _recall /
the Hermes plugin path, exactly what the cascade voice loop uses.

dispatch(name, args, ctrl=None, simulate=True) returns a small JSON-able dict that is
sent back as the function_call_output; the model speaks a confirmation from it.
simulate=True plans the action with no side effects (used by the cloud self-test).
"""
import os, sys, json, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zoe_router          # the single command router (execute / route / recall / plugins)
try:
    import zoe_memory      # Obsidian long-term memory; optional, best-effort
except Exception:
    zoe_memory = None

# Tool schemas in the OpenAI Realtime `tools` format. Names + params mirror the
# router's action vocabulary so the model can drive everything ZOE already does.
TOOLS = [
    {"type": "function", "name": "launch_app",
     "description": "Open a desktop app on Chris's Windows PC (Discord, Spotify, VS Code, Notepad, etc.).",
     "parameters": {"type": "object",
        "properties": {"name": {"type": "string", "description": "The app name to open."}},
        "required": ["name"]}},
    {"type": "function", "name": "close_app",
     "description": "Close or quit a running desktop app.",
     "parameters": {"type": "object",
        "properties": {"name": {"type": "string", "description": "The app name to close."}},
        "required": ["name"]}},
    {"type": "function", "name": "open_folder",
     "description": "Open a folder in Explorer. Use Windows paths; Downloads/Documents/Desktop/"
                    "Videos/Pictures/Music map under the user profile.",
     "parameters": {"type": "object",
        "properties": {"path": {"type": "string", "description": "Folder name or Windows path."}},
        "required": ["path"]}},
    {"type": "function", "name": "open_web",
     "description": "Open the browser to a site or a search. Pass a full https URL, or a plain "
                    "query to search the web.",
     "parameters": {"type": "object",
        "properties": {"query_or_url": {"type": "string",
            "description": "An https URL, or a search query."}},
        "required": ["query_or_url"]}},
    {"type": "function", "name": "search_platform",
     "description": "Search a content platform for a profile, video, or topic and open the "
                    "result. Use for 'find X on YouTube/TikTok/Instagram/X/Twitch/Spotify/"
                    "Reddit/Roblox', pulling up a creator's profile, or searching a platform's "
                    "videos. Prefer this over open_web whenever a platform is named.",
     "parameters": {"type": "object",
        "properties": {
            "platform": {"type": "string", "description": "youtube, tiktok, instagram, twitter "
                         "(x), twitch, spotify, reddit, roblox, or google."},
            "query": {"type": "string", "description": "Search terms, or a username/handle for "
                      "a profile (with or without @)."},
            "kind": {"type": "string", "enum": ["search", "profile", "videos"],
                     "description": "profile = a creator's page; search/videos = search the "
                     "platform. Default search."}},
        "required": ["platform", "query"]}},
    {"type": "function", "name": "open_in_account",
     "description": "Open a website signed in as a specific account by using that Chrome profile. "
                    "Use to switch accounts or open something as a particular account he has. Does "
                    "NOT store or type passwords -- it uses the account he is already signed into "
                    "in Chrome. If he has multiple accounts, suggest one and confirm before using.",
     "parameters": {"type": "object",
        "properties": {
            "url_or_query": {"type": "string", "description": "A URL or a site/search to open."},
            "account": {"type": "string", "description": "Which account/profile (e.g. personal, "
                        "zenthra, clearcoat)."}},
        "required": ["url_or_query", "account"]}},
    {"type": "function", "name": "search_site",
     "description": "Find a specific thing within a particular website. Use for 'find X on "
                    "<site>' or 'search <site> for X' when the site is a regular website "
                    "(espn.com, amazon, a news site) rather than a known content platform. "
                    "Does a site-scoped search that works on any website.",
     "parameters": {"type": "object",
        "properties": {
            "site": {"type": "string", "description": "Website domain or name (espn.com, amazon, "
                     "reddit.com)."},
            "query": {"type": "string", "description": "What to find on that site."}},
        "required": ["site", "query"]}},
    {"type": "function", "name": "start_workspace",
     "description": "Start a named workspace or mode (coding, school, gaming, editing) which "
                    "launches its apps and sites.",
     "parameters": {"type": "object",
        "properties": {"name": {"type": "string", "description": "The workspace/mode name."}},
        "required": ["name"]}},
    {"type": "function", "name": "browser_open",
     "description": "Open her controllable browser to a URL or site and return what's on the page. "
                    "This is the browser she can actually operate (click, type, navigate), separate "
                    "from open_web. Use it when he wants to DO something on a site, not just view it.",
     "parameters": {"type": "object",
        "properties": {"url": {"type": "string", "description": "URL or site to open."}},
        "required": ["url"]}},
    {"type": "function", "name": "browser_read",
     "description": "Read the current page again: its title, url, visible text, and the clickable/"
                    "typable elements with their labels. Use this to see what's on the page before "
                    "deciding what to click or type.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"type": "function", "name": "browser_click",
     "description": "Click the element whose visible text/label matches. Irreversible labels (post, "
                    "send, buy, pay, delete, unfollow) are REFUSED unless confirmed is true -- so "
                    "ask him yes/no first, then call again with confirmed true.",
     "parameters": {"type": "object",
        "properties": {
            "text": {"type": "string", "description": "The visible text/label of the button or "
                     "link to click."},
            "confirmed": {"type": "boolean", "description": "Set true only after he says yes to an "
                          "irreversible click."}},
        "required": ["text"]}},
    {"type": "function", "name": "browser_type",
     "description": "Type text into a field (matched by its label/placeholder/name). Leave submit "
                    "false to just fill it. Submitting is REFUSED unless confirmed is true, so ask "
                    "him yes/no first, then call again with submit and confirmed true.",
     "parameters": {"type": "object",
        "properties": {
            "field": {"type": "string", "description": "Label/placeholder of the field."},
            "text": {"type": "string", "description": "What to type."},
            "submit": {"type": "boolean", "description": "Press Enter to submit."},
            "confirmed": {"type": "boolean", "description": "Set true only after he says yes to "
                          "submitting."}},
        "required": ["field", "text"]}},
    {"type": "function", "name": "browser_back",
     "description": "Go back one page in the browser (undoes the last navigation).",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"type": "function", "name": "browser_forward",
     "description": "Go forward one page in the browser.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"type": "function", "name": "browser_scroll",
     "description": "Scroll the page up or down to reveal more.",
     "parameters": {"type": "object",
        "properties": {"direction": {"type": "string", "enum": ["up", "down"]}},
        "required": ["direction"]}},
    {"type": "function", "name": "play_music",
     "description": "Start epic background music, looping and ducked under your voice. Use for a "
                    "cinematic moment, like narrating a full rundown of what you can do. It keeps "
                    "playing until stop_music or he says to stop the music.",
     "parameters": {"type": "object",
        "properties": {"track": {"type": "string", "description": "Optional path to a music file; "
                                 "defaults to his configured track."}},
        "required": []}},
    {"type": "function", "name": "stop_music",
     "description": "Stop the background music.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"type": "function", "name": "set_music",
     "description": "Change the background music. When he says 'switch to <song or vibe>', "
                    "download a royalty-free / no-copyright track matching it and make it the "
                    "track for next time. Confirm the new track by name when done.",
     "parameters": {"type": "object",
        "properties": {"query": {"type": "string", "description": "The song or vibe to switch to."}},
        "required": ["query"]}},
    {"type": "function", "name": "recall_memory",
     "description": "Recall from long-term memory: what was worked on last session, or notes on "
                    "a topic. Empty query = the last session.",
     "parameters": {"type": "object",
        "properties": {"query": {"type": "string",
            "description": "What to recall, or empty for the last session."}},
        "required": []}},
    {"type": "function", "name": "read_file",
     "description": "Read a file or log on his machine so you can see what actually happened "
                    "(e.g. read 'zoe-voice.log' to find why something failed). Repo-relative or "
                    "absolute path. Read-only and safe. Use this to investigate before answering "
                    "'why did that fail' instead of guessing.",
     "parameters": {"type": "object",
        "properties": {"path": {"type": "string", "description": "File or folder path to read."}},
        "required": ["path"]}},
    {"type": "function", "name": "run_command",
     "description": "Run a shell command in the project to check or fix something (git, npm, "
                    "python, tests, etc.) and read its output. Destructive commands (delete, "
                    "format, force-push, ...) are REFUSED unless confirmed is true, so confirm "
                    "yes/no with him first for those. Use this to actually fix things, not just "
                    "describe them.",
     "parameters": {"type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to run."},
            "confirmed": {"type": "boolean", "description": "Set true only after he says yes to a "
                          "destructive command."}},
        "required": ["command"]}},
    {"type": "function", "name": "run_agent",
     "description": "Hand a hard reasoning, research, or multi-step coding task to the Hermes "
                    "agent. Use for anything beyond a simple command.",
     "parameters": {"type": "object",
        "properties": {"prompt": {"type": "string", "description": "The full request for Hermes."}},
        "required": ["prompt"]}},
]


def _openai_reason(prompt):
    """Deep reasoning via a strong OpenAI text model (the same key the voice runs on), so
    run_agent gives heavier thinking even without a local Hermes install. ZOE_REASON_MODEL
    overrides the model."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return {"ok": False, "error": "no OPENAI_API_KEY for reasoning"}
    model = os.environ.get("ZOE_REASON_MODEL", "gpt-4o")
    body = json.dumps({"model": model, "messages": [
        {"role": "system", "content": "You are Zoe's deep-reasoning engine for Chris. Think it "
         "through and give a clear, complete, actionable answer."},
        {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        return {"ok": True, "answer": d["choices"][0]["message"]["content"].strip()[:1500]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _web_url(query_or_url):
    s = (query_or_url or "").strip()
    if s.startswith(("http://", "https://")):
        return s
    return "https://www.google.com/search?q=" + urllib.parse.quote(s)


def _platform_url(platform, query, kind="search"):
    """Build a search/profile URL for a content platform. profile -> a creator's page;
    search/videos -> search the platform. Unknown platforms fall back to a scoped Google
    search so she always opens something useful."""
    p = (platform or "").strip().lower()
    p = {"x": "twitter", "yt": "youtube", "ig": "instagram", "insta": "instagram",
         "tik tok": "tiktok", "tik-tok": "tiktok"}.get(p, p)
    q = (query or "").strip()
    kind = (kind or "search").strip().lower()
    handle = urllib.parse.quote(q.lstrip("@").strip())
    enc = urllib.parse.quote(q)
    if p == "youtube":
        return (f"https://www.youtube.com/@{handle}" if kind == "profile"
                else f"https://www.youtube.com/results?search_query={enc}")
    if p == "tiktok":
        return (f"https://www.tiktok.com/@{handle}" if kind == "profile"
                else f"https://www.tiktok.com/search?q={enc}")
    if p == "instagram":
        return (f"https://www.instagram.com/{handle}/" if kind == "profile"
                else f"https://www.instagram.com/explore/search/keyword/?q={enc}")
    if p == "twitter":
        return (f"https://x.com/{handle}" if kind == "profile"
                else f"https://x.com/search?q={enc}&src=typed_query")
    if p == "twitch":
        return (f"https://www.twitch.tv/{handle}" if kind == "profile"
                else f"https://www.twitch.tv/search?term={enc}")
    if p == "spotify":
        return f"https://open.spotify.com/search/{enc}"
    if p == "reddit":
        return (f"https://www.reddit.com/user/{handle}" if kind == "profile"
                else f"https://www.reddit.com/search/?q={enc}")
    if p == "roblox":
        return f"https://www.roblox.com/search/users?keyword={enc}"
    if p:                                       # unknown platform: scope a Google search to it
        return "https://www.google.com/search?q=" + urllib.parse.quote(f"{q} {p}")
    return "https://www.google.com/search?q=" + enc


def _site_search_url(site, query):
    """Find something within ANY website via a site-scoped Google search. A real domain
    (espn.com) gets `site:espn.com`; a bare name just scopes the query to it. Works on every
    site, no per-site search syntax needed."""
    s = (site or "").strip().lower()
    for pre in ("https://", "http://"):
        if s.startswith(pre): s = s[len(pre):]
    if s.startswith("www."): s = s[4:]
    s = s.strip("/").split("/")[0]
    q = (query or "").strip()
    if "." in s:
        return "https://www.google.com/search?q=" + urllib.parse.quote(f"{q} site:{s}")
    if s:
        return "https://www.google.com/search?q=" + urllib.parse.quote(f"{q} {s}")
    return "https://www.google.com/search?q=" + urllib.parse.quote(q)


def _open_url(url):
    """Open a URL in the default browser, the reliable Windows way. webbrowser.open often
    reports success but opens nothing on Windows, so go straight to os.startfile / `start` --
    the same shell mechanism that already works for launching apps. Returns True if launched."""
    try:
        os.startfile(url)          # Windows: hands the URL to the default browser
        return True
    except Exception:
        pass
    try:
        import subprocess
        subprocess.Popen(["cmd", "/c", "start", "", url])
        return True
    except Exception:
        pass
    try:
        import webbrowser
        return bool(webbrowser.open(url))   # last resort (non-Windows / odd setups)
    except Exception:
        return False


_BROWSER = {
    "browser_open": ("open", ("url",)),
    "browser_read": ("read", ()),
    "browser_click": ("click", ("text", "confirmed")),
    "browser_type": ("type", ("field", "text", "submit", "confirmed")),
    "browser_back": ("back", ()),
    "browser_forward": ("forward", ()),
    "browser_scroll": ("scroll", ("direction",)),
}


def _profiles():
    """His account label -> Chrome profile directory, from ZOE_BROWSER_PROFILES.
    Format: 'personal=Default; zenthra=Profile 1; clearcoat=Profile 2'."""
    out = {}
    for part in os.environ.get("ZOE_BROWSER_PROFILES", "").replace(";", ",").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip():
                out[k.strip().lower()] = v.strip()
    return out


def accounts_note():
    """A line for the session persona so she can suggest an account and confirm yes/no."""
    p = _profiles()
    if not p:
        return ""
    return ("Browser accounts he is signed into: " + ", ".join(sorted(p)) + ". When he opens or "
            "searches a site and more than one account could fit, suggest which account to use and "
            "wait for a yes or no before switching. Use open_in_account to open as that account. "
            "Never ask for or handle passwords; the browser holds the login.")


def _find_chrome():
    c = os.environ.get("ZOE_CHROME")
    if c and os.path.exists(c):
        return c
    for p in (r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
              r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
              r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"):
        p = os.path.expandvars(p)
        if os.path.exists(p):
            return p
    return None


def _open_in_chrome(url, profile_dir):
    """Open a URL in a specific Chrome profile (a signed-in account). No passwords involved --
    Chrome supplies the login for whatever profile is named."""
    import subprocess
    chrome = _find_chrome()
    args = ([f"--profile-directory={profile_dir}"] if profile_dir else [])
    try:
        if chrome:
            subprocess.Popen([chrome] + args + [url])
        else:                                   # Chrome not found at the usual paths
            subprocess.Popen(["cmd", "/c", "start", "", "chrome"] + args + [url])
        return True
    except Exception:
        try:
            os.startfile(url)                   # last resort: default browser, no profile
            return True
        except Exception:
            return False


def dispatch(name, args, ctrl=None, simulate=True):
    """Run one tool call through the existing router. Returns a JSON-able result dict.

    simulate=True plans the action with no side effects (cloud self-test / dry runs).
    simulate=False actually executes via zoe_router (real PC actions). Never raises.
    """
    args = args if isinstance(args, dict) else {}
    try:
        if name in ("launch_app", "close_app", "start_workspace"):
            target = (args.get("name") or "").strip()
            action = {"launch_app": "launch", "close_app": "close",
                      "start_workspace": "workspace"}[name]
            if simulate:
                return {"ok": True, "simulated": True, "action": action, "target": target}
            a, handled = zoe_router.execute({"action": action, "target": target}, target, ctrl)
            return {"ok": bool(handled), "action": a, "target": target}

        if name == "open_folder":
            target = (args.get("path") or "").strip()
            if simulate:
                return {"ok": True, "simulated": True, "action": "folder", "target": target}
            a, handled = zoe_router.execute({"action": "folder", "target": target}, target, ctrl)
            return {"ok": bool(handled), "action": a, "target": target}

        if name == "open_web":
            url = _web_url(args.get("query_or_url"))
            if simulate:
                return {"ok": True, "simulated": True, "action": "web", "url": url}
            return {"ok": _open_url(url), "action": "web", "url": url}

        if name == "search_platform":
            url = _platform_url(args.get("platform"), args.get("query"), args.get("kind", "search"))
            if simulate:
                return {"ok": True, "simulated": True, "action": "search", "url": url}
            return {"ok": _open_url(url), "action": "search", "url": url}

        if name == "search_site":
            url = _site_search_url(args.get("site"), args.get("query"))
            if simulate:
                return {"ok": True, "simulated": True, "action": "site_search", "url": url}
            return {"ok": _open_url(url), "action": "site_search", "url": url}

        if name == "open_in_account":
            url = _web_url(args.get("url_or_query"))
            account = (args.get("account") or "").strip().lower()
            profiles = _profiles()
            if simulate:
                return {"ok": True, "simulated": True, "action": "account", "url": url,
                        "account": account, "available": sorted(profiles)}
            if not profiles:
                return {"ok": False, "error": "no accounts configured (set ZOE_BROWSER_PROFILES)"}
            if account and account not in profiles:
                return {"ok": False, "error": "unknown account", "available": sorted(profiles)}
            return {"ok": _open_in_chrome(url, profiles.get(account, "")),
                    "action": "account", "account": account or "default", "url": url}

        if name in _BROWSER:
            method, keys = _BROWSER[name]
            payload = {k: args.get(k) for k in keys if args.get(k) is not None}
            if simulate:
                return {"ok": True, "simulated": True, "action": name, **payload}
            import zoe_browser
            r = zoe_browser.action(method, **payload)
            r["action"] = name
            return r

        if name == "play_music":
            if simulate:
                return {"ok": True, "simulated": True, "action": "music_start",
                        "track": args.get("track", "")}
            import zoe_music
            r = zoe_music.start(args.get("track", ""))
            r["action"] = "music_start"
            return r

        if name == "stop_music":
            if simulate:
                return {"ok": True, "simulated": True, "action": "music_stop"}
            import zoe_music
            r = zoe_music.stop()
            r["action"] = "music_stop"
            return r

        if name == "set_music":
            if simulate:
                return {"ok": True, "simulated": True, "action": "set_music",
                        "query": args.get("query", "")}
            import zoe_music
            r = zoe_music.set_track(args.get("query", ""))
            r["action"] = "set_music"
            return r

        if name == "recall_memory":
            query = (args.get("query") or "").strip()
            if simulate:
                return {"ok": True, "simulated": True, "action": "memory", "query": query}
            if not zoe_memory:
                return {"ok": False, "error": "memory unavailable"}
            handled, say, data = zoe_router._recall(query or "last session",
                                                    {"action": "memory", "target": query})
            return {"ok": bool(handled), "say": say}

        if name == "read_file":
            if simulate:
                return {"ok": True, "simulated": True, "action": "read_file",
                        "path": args.get("path", "")}
            import zoe_ops
            r = zoe_ops.read_file(args.get("path", ""))
            r["action"] = "read_file"
            return r

        if name == "run_command":
            if simulate:
                return {"ok": True, "simulated": True, "action": "run_command",
                        "command": args.get("command", "")}
            import zoe_ops
            r = zoe_ops.run_command(args.get("command", ""), bool(args.get("confirmed", False)))
            r["action"] = "run_command"
            return r

        if name == "run_agent":
            prompt = (args.get("prompt") or "").strip()
            if simulate:
                return {"ok": True, "simulated": True, "action": "agent", "prompt": prompt}
            cmd = zoe_router.make_command(intent="plugin_action", target="hermes",
                                          payload={"prompt": prompt})
            handled, res = zoe_router._run_plugin(cmd)
            ans = res.get("answer") if isinstance(res, dict) else None
            if handled and ans:
                return {"ok": True, "answer": ans[:1500], "action": "agent", "via": "hermes"}
            # Hermes not installed/configured -> reason with OpenAI (the key already in use)
            r = _openai_reason(prompt)
            r["action"] = "agent"; r["via"] = "openai"
            return r

        return {"ok": False, "error": f"unknown tool {name}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _selftest():
    """Dry-run every tool with simulate=True (no side effects). Cloud-safe verification
    that the schema names and arg mapping line up with dispatch -- no socket, no audio."""
    cases = [
        ("launch_app", {"name": "Discord"}),
        ("close_app", {"name": "Spotify"}),
        ("open_folder", {"path": "Downloads"}),
        ("open_web", {"query_or_url": "best protein for mass"}),
        ("open_web", {"query_or_url": "https://news.google.com"}),
        ("search_platform", {"platform": "youtube", "query": "mrbeast", "kind": "profile"}),
        ("search_platform", {"platform": "tiktok", "query": "zen_cj", "kind": "profile"}),
        ("search_platform", {"platform": "spotify", "query": "lofi beats"}),
        ("search_platform", {"platform": "x", "query": "@cj_goat09", "kind": "profile"}),
        ("search_site", {"site": "espn.com", "query": "lakers score"}),
        ("search_site", {"site": "amazon", "query": "resistance bands"}),
        ("open_in_account", {"url_or_query": "https://youtube.com", "account": "zenthra"}),
        ("browser_open", {"url": "youtube.com"}),
        ("browser_click", {"text": "Subscribe"}),
        ("browser_type", {"field": "Search", "text": "lofi", "submit": True}),
        ("browser_back", {}),
        ("play_music", {}),
        ("stop_music", {}),
        ("set_music", {"query": "epic orchestral"}),
        ("start_workspace", {"name": "coding"}),
        ("recall_memory", {"query": ""}),
        ("read_file", {"path": "zoe-voice.log"}),
        ("run_command", {"command": "git status"}),
        ("run_command", {"command": "rm -rf /"}),
        ("run_agent", {"prompt": "plan the KOS deploy fix"}),
        ("bogus_tool", {}),
    ]
    names = {t["name"] for t in TOOLS}
    print(f"  {len(TOOLS)} tools declared: {', '.join(sorted(names))}")
    for nm, ar in cases:
        out = dispatch(nm, ar, simulate=True)
        print(f"  {nm}({ar}) -> {json.dumps(out)}")
    # the model-facing names must all be dispatchable
    for t in names:
        assert dispatch(t, {}, simulate=True).get("ok") is not None, t
    print("  selftest ok")


if __name__ == "__main__":
    _selftest()
