# Roblox Toolbox Model Virus: Removal and Prevention

You inserted a free model from the Studio Toolbox and now a "virus" keeps
showing up in your game. This guide gets it out and keeps it out.

## What this actually is

Free Toolbox models can hide malicious `Script` and `LocalScript` instances
inside them. The common kinds:

- **Self-replicators.** They clone themselves into many places in the game, so
  deleting one copy does nothing. The rest re-spread it.
- **Spammers.** They flood your game with decals, parts, signs, or chat
  messages.
- **Backdoors.** The dangerous kind. A short script `require()`s a remote asset
  or runs `loadstring`, which means the person who uploaded the model can run
  code in YOUR game whenever they want. That is how people get their games
  wiped or hijacked.

The reason it "keeps coming back" is the self-replication. You have to find
every copy at once, not one at a time.

## Immediate triage (do this first)

1. **Back up the place file.** File → Save to File (`.rbxl`) before you touch
   anything, so you can roll back if you delete the wrong thing.

2. **List every script.** In the Explorer panel, click the filter box at the
   top and type `Script`. Now every `Script` and `LocalScript` in the place is
   visible at once.

3. **Spot the ones you did not write.** Red flags:
   - Names you do not recognize, or random gibberish names.
   - Scripts hidden inside parts, decals, meshes, or unexpected places.
   - Scripts disabled but still present (a planted dormant copy).

4. **Search inside all scripts.** Press `Ctrl+Shift+F` (Find in All Scripts)
   and search for each red-flag token from the table below. Delete every match
   that is not yours.

5. **Cut the phone-home while you clean.** Game Settings → Security: turn OFF
   **Allow HTTP Requests** and **Allow Studio Access to API Services**. This
   stops a backdoor from reaching the internet or its remote asset while you
   work. Turn them back on later only if a real feature needs them.

## Red-flag tokens

If a script you did not write contains any of these, treat it as hostile.

| Token | Why it is dangerous |
|---|---|
| `require(123456789)` (a number) | Loads and runs a remote module by asset ID. The classic backdoor delivery. |
| `loadstring(` | Runs a string as live code. Lets a backdoor execute anything fetched at runtime. |
| `HttpService`, `:GetAsync`, `HttpGet`, `GetAsync` | Pulls code or commands from an external server. |
| `getfenv` / `setfenv` | Hides or rewrites the script environment to dodge detection. |
| `game:GetObjects(` | Inserts more assets (often the rest of the virus) from a URL or asset ID. |
| `MarketplaceService` in odd places | Sometimes used to fetch payloads or fingerprint the game. |
| Long base64 / random string blobs | Obfuscated payload. Legitimate scripts are readable; this is not. |
| `string.char(104, 116, ...)` chains | Builds hidden strings character by character to hide a URL or command. |
| `\0` padding / unreadable characters | Used to push malicious code off-screen so you scroll past it. |

A normal gameplay script does not need `require` by number, `loadstring`, or
HTTP calls. If you see those in something you did not author, delete it.

## Ready-to-paste scanner

Open the **Command Bar** at the bottom of Studio (View → Command Bar) and paste
this. It is read-only: it only prints suspicious scripts, it does not delete
anything. Then you go delete the ones it flags.

```lua
-- Roblox backdoor / virus scanner (read-only, prints findings)
local FLAGS = {
	"require%s*%(%s*%d",      -- require( by asset id
	"loadstring",
	"HttpGet",
	"GetAsync",
	"getfenv",
	"setfenv",
	"GetObjects",
	"\\0",                     -- null padding used to hide code
}

local hits = 0
for _, inst in ipairs(game:GetDescendants()) do
	if inst:IsA("LuaSourceContainer") then
		local ok, src = pcall(function() return inst.Source end)
		if ok and src then
			for _, pattern in ipairs(FLAGS) do
				if src:find(pattern) then
					hits += 1
					warn(("[SUSPICIOUS] %s  ->  matched '%s'"):format(inst:GetFullName(), pattern))
					break
				end
			end
		end
	end
end

if hits == 0 then
	print("Scan complete. No suspicious scripts found.")
else
	warn(("Scan complete. %d suspicious script(s) flagged above. Review and delete the ones you did not write."):format(hits))
end
```

Note: reading `.Source` from the Command Bar requires script editing access,
which Studio has by default for the place owner. If `.Source` comes back empty
for a script, that script is itself a red flag (something is blocking you from
reading it).

Optional second pass: list **every** script and its location so you can eyeball
anything the token list missed.

```lua
-- List all scripts and where they live
for _, inst in ipairs(game:GetDescendants()) do
	if inst:IsA("LuaSourceContainer") then
		print(("%s  (%s)"):format(inst:GetFullName(), inst.ClassName))
	end
end
```

## Prevention (so this never happens again)

- **Never insert-and-run a model blind.** Insert it into a throwaway baseplate
  first. Run the scanner, read the scripts, then move only the clean parts into
  your real game.
- **Prefer trusted creators.** On the Toolbox, sort by and favor items with high
  review counts and a real creator history. "Free Admin," "Aimbot," and "Free
  Money" models are bait.
- **Use a maintained anti-backdoor plugin.** Search the plugin marketplace for a
  current, well-reviewed virus/backdoor scanner and let it sweep before you
  publish. Pick by recent reviews, not by name, since which plugin is trusted
  changes over time.
- **Keep HTTP and API services off** unless a specific feature needs them. A
  backdoor with no internet access is far less useful to an attacker.
- **Back up before risky inserts.** Save a `.rbxl` so a bad insert is one undo,
  not a rebuild.

## If it already shipped to a live game

1. Take the game offline or roll the published version back to a known-clean
   save.
2. Clean the local place with the steps above, run the scanner until it reports
   zero, then re-publish.
3. Roblox places do not store passwords, so there is nothing to "reset." But if
   your game uses `HttpService` to talk to your own server (a webhook, a
   database, an API), assume a backdoor could have seen those URLs and keys.
   Rotate any such endpoint keys and check that server's logs for unexpected
   calls.
4. Only re-publish after a clean scan. Republishing a still-infected place just
   re-ships the virus to your players.
