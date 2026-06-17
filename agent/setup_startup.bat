@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo   Minecraft Panel Agent Startup Installer (Windows)
echo ===================================================
echo.
echo Detecting current folder path: "%~dp0"
echo.

:: Run PowerShell script block to create the startup shortcut pointing to the new folder
powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\MinecraftAgent.lnk\"); $Shortcut.TargetPath = '%~dp0start_agent.vbs'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Startup shortcut created in Windows Startup folder!
    echo The agent will now launch silently in the background on every PC boot.
    echo.
) else (
    echo.
    echo [ERROR] Failed to create startup shortcut.
    echo.
)

pause
