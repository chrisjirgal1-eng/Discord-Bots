' Zoe auto-start: launch the Electron desktop app at login.
' Console window is hidden (style 0); the Zoe app window still shows. A shortcut to this
' file lives in the Windows Startup folder. Falls back to the voice-only assistant if
' Electron is not installed.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
el = root & "\node_modules\electron\dist\electron.exe"
If fso.FileExists(el) Then
  sh.CurrentDirectory = root
  sh.Run """" & el & """ """ & root & """", 0, False
Else
  py = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Python\pythoncore-3.14-64\pythonw.exe"
  If Not fso.FileExists(py) Then py = "pythonw"
  sh.Run """" & py & """ """ & root & "\tools\zoe_assistant.py""", 0, False
End If
