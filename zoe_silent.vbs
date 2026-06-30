' ZOE launcher: open the Electron desktop app (the UI) which auto-starts the realtime voice.
' Double-click this. The app has a single-instance lock, so opening it twice just focuses the
' existing window. If the Electron build isn't present, falls back to the voice-only script
' (logged to zoe.log). To auto-run at login, drop a shortcut to this in shell:startup.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
q = Chr(34)
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root

' clear any stray copy (old direct-run voice or a previous app instance) so nothing stacks
ps = "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*zoe_realtime.py*' -or ($_.Name -eq 'electron.exe' -and $_.CommandLine -like '*" & root & "*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
sh.Run "powershell -NoProfile -Command " & q & ps & q, 0, True

' A force-killed/crashed app leaves a stale single-instance lockfile in userData; the next launch
' then sees the lock and quits instantly (looks like "the app won't open"). Remove it before launch.
sh.Run "powershell -NoProfile -Command " & q & "Remove-Item (Join-Path $env:APPDATA 'zoe-desktop\lockfile') -Force -ErrorAction SilentlyContinue" & q, 0, True

el = root & "\node_modules\electron\dist\electron.exe"
If fso.FileExists(el) Then
  sh.Run q & el & q & " " & q & root & q, 1, False      ' open the app, visible window
Else
  ' no Electron build -> run the realtime voice directly, hidden, logged to zoe.log
  py = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe")
  If Not fso.FileExists(py) Then py = "python"
  sh.Run "cmd /c " & q & py & q & " -u tools\zoe_realtime.py >> zoe.log 2>&1", 0, False
End If
