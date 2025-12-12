' Setup Telegram Bot Auto-Start (No Admin Required)
' This creates a Windows Task that runs on login

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get script directory
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strProjectDir = objFSO.GetParentFolderName(strScriptDir)
strBatFile = strScriptDir & "\start_telegram_bot.bat"

' Create Task Scheduler task using schtasks.exe (no admin needed for user tasks)
strTaskName = "AgentFactoryTelegramBot"
strCommand = "schtasks /Create /SC ONLOGON /TN """ & strTaskName & """ /TR ""cmd /c """" & strBatFile & """""" /RL HIGHEST /F"

' Delete existing task if present
objShell.Run "schtasks /Delete /TN """ & strTaskName & """ /F", 0, True

' Create new task
intResult = objShell.Run(strCommand, 0, True)

If intResult = 0 Then
    ' Start the task now
    objShell.Run "schtasks /Run /TN """ & strTaskName & """", 0, True

    WScript.Sleep 3000

    ' Show success message
    MsgBox "✓ Telegram Bot Auto-Start Enabled!" & vbCrLf & vbCrLf & _
           "The bot will now:" & vbCrLf & _
           "  • Start automatically when you log in" & vbCrLf & _
           "  • Run in the background" & vbCrLf & _
           "  • Logs saved to: logs\telegram_bot.log" & vbCrLf & vbCrLf & _
           "The bot is running now. Test it in Telegram!", _
           vbInformation, "Agent Factory Setup"
Else
    MsgBox "✗ Setup failed (Error " & intResult & ")" & vbCrLf & vbCrLf & _
           "Try running scripts\start_telegram_bot.bat manually", _
           vbCritical, "Agent Factory Setup"
End If
