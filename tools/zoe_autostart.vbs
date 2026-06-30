' Zoe auto-start: launch the Electron desktop app at login, HIDDEN in the tray.
' Console window is hidden (style 0) and the app starts with --hidden so the Zoe window stays in
' the tray, listening; say "hey zoe" to open it. A shortcut to this file lives in the Windows
' Startup folder (run tools\zoe_install_autostart.ps1). Falls back to the voice-only assistant.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
el = root & "\node_modules\electron\dist\electron.exe"
If fso.FileExists(el) Then
  sh.CurrentDirectory = root
  sh.Run """" & el & """ """ & root & """ --hidden", 0, False
Else
  py = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Python\pythoncore-3.14-64\pythonw.exe"
  If Not fso.FileExists(py) Then py = "pythonw"
  sh.Run """" & py & """ -u """ & root & "\tools\zoe_realtime.py""", 0, False
End If
