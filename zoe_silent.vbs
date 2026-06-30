' ZOE silent launcher: runs her in the background with NO console window.
' Double-click this (or drop a shortcut in shell:startup to auto-run at login).
' Everything she prints goes to zoe.log in this folder, so if she ever goes quiet,
' open zoe.log in Notepad to see what happened -- no terminal needed.
'
' Hidden mode has no window to press Enter in, so she needs a way to wake by voice:
'   - a DEEPGRAM_API_KEY in .env  -> say "Hey Zoe" to wake her (cheap, idles free), OR
'   - ZOE_REALTIME_GATE=always in .env -> she listens the moment she starts (costs more).

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root

py = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe")
If Not fso.FileExists(py) Then py = "python"

' run hidden (window style 0), don't wait; -u = unbuffered so zoe.log is live
sh.Run "cmd /c """ & py & """ -u tools\zoe_realtime.py >> zoe.log 2>&1", 0, False
