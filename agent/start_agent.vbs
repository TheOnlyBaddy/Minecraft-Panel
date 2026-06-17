Set objFSO = CreateObject("Scripting.FileSystemObject")
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")

' Change directory to the agent folder so that config.json is loaded correctly
WshShell.CurrentDirectory = strScriptPath

' Run agent.py silently in the background using pythonw
WshShell.Run "pythonw.exe """ & strScriptPath & "\agent.py""", 0, False
