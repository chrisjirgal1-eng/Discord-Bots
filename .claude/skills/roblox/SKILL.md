---
name: roblox
description: Work on Chris's Roblox game (Zenthra) in Roblox Studio - open it, understand the screen, operate Studio, and write/test Luau, using awareness + screen control.
---

# Roblox Studio workflow

How Zoe builds in Roblox. Studio is installed at `%LOCALAPPDATA%\Roblox\Versions\*\RobloxStudioBeta.exe`. Chris's games save to the Roblox cloud (no local place files, no Rojo yet).

## The loop
1. **Open Studio** - `roblox` tool with action `open` (or launch the exe). Wait for it to load.
2. **Get awareness** - `see_screen` to read the current state: the Explorer (right), the Toolbox, the 3D Viewport, and the Output/Script editor. Describe what's there before acting.
3. **Operate Studio** - `screen_task` (Look-Plan-Act-Verify). Common moves:
   - Insert an object: click a part in Explorer -> right-click -> Insert Object, or use the Model/Home ribbon.
   - Open a script: double-click a Script/LocalScript in the Explorer to open the editor.
   - Run/stop: press F5 to Play (test), Shift+F5 to stop. Watch the Output window for errors.
4. **Write Luau**:
   - Preferred (robust): if a **Rojo** project exists, write `.luau` files with the coding tools and let Rojo sync into Studio. Not set up yet -> offer to set it up.
   - Fallback (now): open the Script in the editor (screen_task) and type the code via `control_screen`/screen_task. Keep scripts small so it is verifiable.
5. **Test + iterate**: Play (F5), read the Output via `see_screen`, fix, repeat. Confirm before publishing.

## Luau notes (so the code is correct)
- `Script` runs server-side; `LocalScript` runs on the client; `ModuleScript` is required by others.
- Services: `local Players = game:GetService("Players")`, `RunService`, `ReplicatedStorage`, `Workspace`.
- Events: `part.Touched:Connect(function(hit) ... end)`; `Players.PlayerAdded:Connect(...)`.
- Create: `local p = Instance.new("Part"); p.Parent = workspace`.
- Prefer clear, commented, small scripts; test each before adding more.

## When Chris asks for a bigger system
Recommend setting up **Rojo** (file-based sync) so Zoe can code Luau reliably as files and version it - much stronger than typing into the editor through the screen. Ask before installing/changing his workflow.

## Safety
Confirm before Publish, deleting instances, or anything that touches the live game. Build and test locally first.
