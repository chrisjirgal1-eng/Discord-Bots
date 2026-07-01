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
4. **Write Luau (Rojo IS set up)**:
   - Start the sync: `roblox` action `serve` (runs `rojo serve` on `RobloxProjects/zenthra`).
   - In Studio, connect the **Rojo plugin** once (install "Rojo" from the Studio plugin marketplace; guide Chris via screen_task if needed), then click Connect.
   - Write scripts with `roblox_script` (name, code, side = server/client/shared). They land as files in `src/` and sync into Studio live. This is the robust path - prefer it over typing in the editor.
   - Keep scripts small; test each.
5. **Test + iterate**: Play (F5), read the Output via `see_screen`, fix, repeat. Confirm before publishing.

## Luau notes (so the code is correct)
- `Script` runs server-side; `LocalScript` runs on the client; `ModuleScript` is required by others.
- Services: `local Players = game:GetService("Players")`, `RunService`, `ReplicatedStorage`, `Workspace`.
- Events: `part.Touched:Connect(function(hit) ... end)`; `Players.PlayerAdded:Connect(...)`.
- Create: `local p = Instance.new("Part"); p.Parent = workspace`.
- Prefer clear, commented, small scripts; test each before adding more.

## When Chris asks for a bigger system
Rojo is installed and the project exists, so build with files: `roblox_script` for each script, keep logic modular (ModuleScripts on the shared side), start `roblox serve`, and test in Studio after each change. This scales far better than editor typing.

## Safety
Confirm before Publish, deleting instances, or anything that touches the live game. Build and test locally first.
