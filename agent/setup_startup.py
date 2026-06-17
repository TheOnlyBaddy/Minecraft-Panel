import os
import subprocess

def setup():
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(agent_dir, "start_agent.bat")
    vbs_path = os.path.join(agent_dir, "start_agent.vbs")

    # 1. Resolve Python executable path
    venv_py = os.path.abspath(os.path.join(agent_dir, "..", "backend", ".venv", "Scripts", "python.exe"))
    if os.path.exists(venv_py):
        python_cmd = f'"{venv_py}"'
    else:
        python_cmd = "python"

    # Create start_agent.bat
    bat_content = f'@echo off\ncd /d "{agent_dir}"\n{python_cmd} agent.py\n'
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"Created: {bat_path}")

    # 2. Create start_agent.vbs (silently launches bat file)
    vbs_content = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run "cmd.exe /c \\"" & "{bat_path}" & "\\"\\"", 0, false\n'
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)
    print(f"Created: {vbs_path}")

    # 3. Create shortcut in Windows Startup folder via PowerShell
    startup_dir = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
    lnk_path = os.path.join(startup_dir, "MinecraftPanelAgent.lnk")

    ps_script = f"""
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut("{lnk_path}")
    $Shortcut.TargetPath = "{vbs_path}"
    $Shortcut.WorkingDirectory = "{agent_dir}"
    $Shortcut.Save()
    """
    
    try:
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        print(f"Successfully registered agent startup shortcut at: {lnk_path}")
        print("The Minecraft Panel Agent will now run silently in the background whenever you log into Windows.")
    except Exception as e:
        print(f"Failed to register startup shortcut: {e}")

if __name__ == "__main__":
    setup()
