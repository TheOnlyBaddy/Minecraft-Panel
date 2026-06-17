import os
import sys
import json
import re
import time
import asyncio
import shutil
import zipfile
import websockets
import psutil
from datetime import datetime, timezone

# Load Configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

BACKEND_URL = config["backend_url"]
AGENT_TOKEN = config["agent_token"]
SERVER_DIR = os.path.abspath(config["server_dir"])
JAR_NAME = config["jar_name"]
MIN_RAM = config["min_ram"]
MAX_RAM = config["max_ram"]

def is_ws_open(ws):
    if not ws:
        return False
    if hasattr(ws, "state"):
        try:
            return ws.state.name == "OPEN"
        except AttributeError:
            pass
    return getattr(ws, "open", False)

class LocalAgent:
    def __init__(self):
        self.status = "STOPPED"
        self.process = None
        self.playit_process = None
        self.active_players_set = set()
        self.log_readers = []
        self.ws = None
        self.loop = None
        self.server_dir = SERVER_DIR
        os.makedirs(self.server_dir, exist_ok=True)

    def get_metrics(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(self.server_dir)
        
        return {
            "cpu_percent": cpu,
            "memory_used": mem.used,
            "memory_total": mem.total,
            "disk_used": disk.used,
            "disk_total": disk.total,
            "active_players": len(self.active_players_set),
            "active_players_list": sorted(list(self.active_players_set)),
            "server_status": self.status
        }

    async def start_server(self):
        if self.status in ("STARTING", "RUNNING"):
            return {"status": "error", "detail": "Server already active"}

        self.active_players_set.clear()
        jar_path = os.path.join(self.server_dir, JAR_NAME)
        if not os.path.exists(jar_path):
            with open(jar_path, "w") as f:
                f.write("# Placeholder for Paper JAR")

        # Build commands
        if os.name == "nt":
            bat_path = os.path.join(self.server_dir, "start.bat")
            if os.path.exists(bat_path):
                cmd = ["cmd.exe", "/c", "start.bat"]
            else:
                cmd = ["java", f"-Xms{MIN_RAM}", f"-Xmx{MAX_RAM}", "-jar", JAR_NAME, "nogui"]
        else:
            sh_path = os.path.join(self.server_dir, "start.sh")
            if os.path.exists(sh_path):
                cmd = ["/bin/sh", "start.sh"]
            else:
                cmd = ["java", f"-Xms{MIN_RAM}", f"-Xmx{MAX_RAM}", "-jar", JAR_NAME, "nogui"]

        try:
            self.status = "STARTING"
            await self.send_status_update()
            await self.send_log("[Agent]: Spawning Minecraft child subprocess locally...")

            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.server_dir
            )

            # Start streams readers
            self.log_readers = [
                asyncio.create_task(self.read_stream(self.process.stdout, "stdout")),
                asyncio.create_task(self.read_stream(self.process.stderr, "stderr"))
            ]
            asyncio.create_task(self.process_watcher())

            # Start playit tunnel if exists
            await self.start_playit()

            return {"status": "success", "detail": "Server start initiated"}
        except Exception as e:
            self.status = "STOPPED"
            await self.send_status_update()
            await self.send_log(f"[Agent Error]: Failed to start subprocess: {str(e)}")
            return {"status": "error", "detail": str(e)}

    async def start_playit(self):
        playit_bin = "playit.exe" if os.name == "nt" else "playit"
        playit_path = os.path.join(self.server_dir, playit_bin)
        if not os.path.exists(playit_path):
            import shutil
            system_playit = shutil.which(playit_bin)
            if system_playit:
                playit_path = system_playit

        if os.path.exists(playit_path):
            await self.send_log(f"[Agent]: Found playit.gg at {playit_path}. Launching tunnel...")
            try:
                self.playit_process = await asyncio.create_subprocess_exec(
                    playit_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.server_dir
                )
                asyncio.create_task(self.read_playit_stream(self.playit_process.stdout))
                asyncio.create_task(self.read_playit_stream(self.playit_process.stderr))
            except Exception as e:
                await self.send_log(f"[Agent Warning]: Failed to start playit.gg: {str(e)}")

    async def stop_server(self):
        if not self.process or self.status == "STOPPED":
            return {"status": "error", "detail": "Server is not running"}

        self.status = "STOPPING"
        await self.send_status_update()
        await self.send_log("[Agent]: Sending stop command to Minecraft console...")
        await self.write_stdin("stop")

        # Wait 30 seconds
        for _ in range(30):
            if self.status == "STOPPED":
                return {"status": "success"}
            await asyncio.sleep(1)

        await self.send_log("[Agent Warning]: Stop timed out. Force killing...")
        await self.kill_server()
        return {"status": "success", "detail": "Force killed"}

    async def kill_server(self):
        if not self.process:
            return {"status": "error", "detail": "Server not active"}
        try:
            self.process.kill()
            await self.send_log("[Agent]: Minecraft subprocess killed via SIGKILL.")
        except Exception:
            pass
        finally:
            self.cleanup_processes()
        return {"status": "success"}

    def cleanup_processes(self):
        if self.playit_process:
            try:
                self.playit_process.kill()
            except Exception:
                pass
            self.playit_process = None

        for reader in self.log_readers:
            if not reader.done():
                reader.cancel()
        self.log_readers.clear()

        self.active_players_set.clear()
        self.process = None
        self.status = "STOPPED"
        asyncio.create_task(self.send_status_update())

    async def process_watcher(self):
        exit_code = await self.process.wait()
        await self.send_log(f"[Agent]: Subprocess exited with code {exit_code}")
        self.cleanup_processes()

    async def write_stdin(self, command: str):
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write((command.strip() + "\n").encode("utf-8"))
                await self.process.stdin.drain()
            except Exception as e:
                await self.send_log(f"[Agent Error]: Failed to write stdin: {str(e)}")

    async def read_stream(self, stream, name: str):
        import codecs
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        buffer = ""
        while True:
            try:
                chunk = await stream.read(1024)
                if not chunk:
                    buffer += decoder.decode(b"", final=True)
                    if buffer:
                        await self.process_log_line(buffer)
                    break
                buffer += decoder.decode(chunk, final=False)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    await self.process_log_line(line)
                if "Press any key to continue" in buffer:
                    await self.process_log_line(buffer)
                    buffer = ""
                    await self.write_stdin("")
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.send_log(f"[Agent Error]: Stream read failure ({name}): {str(e)}")
                break

    async def read_playit_stream(self, stream):
        try:
            while True:
                line_bytes = await stream.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode('utf-8', errors='replace').strip()
                if line:
                    await self.send_log(f"[playit.gg]: {line}")
        except Exception:
            pass

    async def process_log_line(self, line: str):
        line = line.strip()
        if not line:
            return
        await self.send_log(line)

        # State updates
        if self.status == "STARTING" and ("Done (" in line or "For help, type" in line):
            self.status = "RUNNING"
            await self.send_status_update()
            await self.send_log("[Agent]: Server boot detected. Status changed to RUNNING.")

        # Player parse
        if " joined the game" in line:
            idx = line.find(" joined the game")
            colon = line.rfind("]: ", 0, idx)
            username = line[colon + 3:idx].strip() if colon != -1 else line[:idx].strip()
            if " " in username:
                username = username.split()[-1]
            username = re.sub(r'\x1B\s*(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', username).strip()
            if username:
                self.active_players_set.add(username)
        elif " left the game" in line:
            idx = line.find(" left the game")
            colon = line.rfind("]: ", 0, idx)
            username = line[colon + 3:idx].strip() if colon != -1 else line[:idx].strip()
            if " " in username:
                username = username.split()[-1]
            username = re.sub(r'\x1B\s*(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', username).strip()
            if username:
                self.active_players_set.discard(username)

    # File Operations
    def list_files(self, rel_path: str):
        target_dir = os.path.abspath(os.path.join(self.server_dir, rel_path.lstrip("/")))
        if not target_dir.startswith(self.server_dir):
            return {"status": "error", "detail": "Access Denied"}
        if not os.path.exists(target_dir):
            return {"status": "error", "detail": "Folder does not exist"}
        
        items = []
        for name in os.listdir(target_dir):
            full_p = os.path.join(target_dir, name)
            is_dir = os.path.isdir(full_p)
            size = os.path.getsize(full_p) if not is_dir else 0
            items.append({"name": name, "isDir": is_dir, "sizeBytes": size})
        return {"status": "success", "items": items}

    def read_file(self, rel_path: str):
        target_file = os.path.abspath(os.path.join(self.server_dir, rel_path.lstrip("/")))
        if not target_file.startswith(self.server_dir):
            return {"status": "error", "detail": "Access Denied"}
        if not os.path.exists(target_file):
            return {"status": "error", "detail": "File not found"}
        try:
            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {"status": "success", "content": content}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def write_file(self, rel_path: str, content: str):
        target_file = os.path.abspath(os.path.join(self.server_dir, rel_path.lstrip("/")))
        if not target_file.startswith(self.server_dir):
            return {"status": "error", "detail": "Access Denied"}
        try:
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def delete_file(self, rel_path: str):
        target = os.path.abspath(os.path.join(self.server_dir, rel_path.lstrip("/")))
        if not target.startswith(self.server_dir):
            return {"status": "error", "detail": "Access Denied"}
        try:
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def create_folder(self, rel_path: str):
        target = os.path.abspath(os.path.join(self.server_dir, rel_path.lstrip("/")))
        if not target.startswith(self.server_dir):
            return {"status": "error", "detail": "Access Denied"}
        try:
            os.makedirs(target, exist_ok=True)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def list_backups(self):
        backups_dir = os.path.join(self.server_dir, "backups")
        if not os.path.exists(backups_dir):
            return {"status": "success", "backups": []}
        backups = []
        for file in os.listdir(backups_dir):
            if file.endswith(".zip"):
                path = os.path.join(backups_dir, file)
                stat = os.stat(path)
                backups.append({
                    "name": file,
                    "sizeBytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                })
        return {"status": "success", "backups": backups}

    def create_backup(self):
        backups_dir = os.path.join(self.server_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = os.path.join(backups_dir, backup_name)
        
        try:
            # Simple zip generation, excluding backup directory itself
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.server_dir):
                    if "backups" in root:
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_arc = os.path.relpath(file_path, self.server_dir)
                        zipf.write(file_path, rel_arc)
            return {"status": "success", "name": backup_name, "sizeBytes": os.path.getsize(backup_path)}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def restore_backup(self, backup_name: str):
        backup_path = os.path.join(self.server_dir, "backups", backup_name)
        if not os.path.exists(backup_path):
            return {"status": "error", "detail": "Backup archive not found"}
        
        try:
            # Empty current directory except backups
            for item in os.listdir(self.server_dir):
                if item == "backups":
                    continue
                path = os.path.join(self.server_dir, item)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            
            # Unzip
            with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                zip_ref.extractall(self.server_dir)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    # Communication Loops
    async def send_log(self, line: str):
        if is_ws_open(self.ws):
            await self.ws.send(json.dumps({
                "type": "log",
                "line": line
            }))

    async def send_status_update(self):
        if is_ws_open(self.ws):
            await self.ws.send(json.dumps({
                "type": "status_update",
                "status": self.status
            }))

    async def handle_message(self, message_str: str):
        try:
            msg = json.loads(message_str)
        except Exception:
            return
        
        mtype = msg.get("type")
        req_id = msg.get("request_id")
        
        response = None
        
        try:
            if mtype == "start_server":
                response = await self.start_server()
            elif mtype == "stop_server":
                response = await self.stop_server()
            elif mtype == "kill_server":
                response = await self.kill_server()
            elif mtype == "write_stdin":
                await self.write_stdin(msg.get("command", ""))
            elif mtype == "list_files":
                response = self.list_files(msg.get("path", ""))
            elif mtype == "read_file":
                response = self.read_file(msg.get("path", ""))
            elif mtype == "write_file":
                response = self.write_file(msg.get("path", ""), msg.get("content", ""))
            elif mtype == "delete_file":
                response = self.delete_file(msg.get("path", ""))
            elif mtype == "create_folder":
                response = self.create_folder(msg.get("path", ""))
            elif mtype == "list_backups":
                response = self.list_backups()
            elif mtype == "create_backup":
                response = self.create_backup()
            elif mtype == "restore_backup":
                response = self.restore_backup(msg.get("backup_name", ""))
        except Exception as e:
            print(f"Error handling message {mtype}: {e}", file=sys.stderr)
            response = {"status": "error", "detail": f"Agent internal error: {str(e)}"}
            
        if response is not None and req_id is not None:
            response["request_id"] = req_id
            response["type"] = f"{mtype}_response"
            try:
                await self.ws.send(json.dumps(response))
            except Exception as e:
                print(f"Error sending response for {mtype}: {e}", file=sys.stderr)

    async def metrics_reporter_loop(self):
        while True:
            try:
                if is_ws_open(self.ws):
                    metrics = self.get_metrics()
                    await self.ws.send(json.dumps({
                        "type": "metrics",
                        "data": metrics
                    }))
            except Exception:
                pass
            await asyncio.sleep(2)

    async def run(self):
        self.loop = asyncio.get_running_loop()
        ws_endpoint = f"{BACKEND_URL.replace('http', 'ws')}/api/agent/ws"
        
        while True:
            print(f"Connecting to Render backend at {ws_endpoint}...")
            try:
                async with websockets.connect(ws_endpoint) as ws:
                    self.ws = ws
                    print("WebSocket connection established. Sending registration...")
                    
                    # Send registration
                    await ws.send(json.dumps({
                        "type": "register",
                        "token": AGENT_TOKEN
                    }))
                    
                    print("Authenticated. Starting message handling and metrics loops.")
                    await self.send_status_update()
                    
                    # Start periodic metrics reporting
                    metrics_task = asyncio.create_task(self.metrics_reporter_loop())
                    
                    # Read messages
                    try:
                        async for message in ws:
                            await self.handle_message(message)
                    except websockets.exceptions.ConnectionClosed:
                        print("Connection closed by server.")
                    finally:
                        metrics_task.cancel()
            except Exception as e:
                print(f"Connection error: {e}. Reconnecting in 5 seconds...")
            
            await asyncio.sleep(5)

if __name__ == "__main__":
    agent = LocalAgent()
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("Shutting down agent.")
