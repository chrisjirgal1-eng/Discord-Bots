' Zoe auto-start: launch the voice assistant hidden (no console window), at login.
' A shortcut to this file lives in the Windows Startup folder. Window style 0 = hidden.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
py = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Python\pythoncore-3.14-64\pythonw.exe"
If Not fso.FileExists(py) Then py = "pythonw"
sh.Run """" & py & """ """ & root & "\tools\zoe_assistant.py""", 0, False
