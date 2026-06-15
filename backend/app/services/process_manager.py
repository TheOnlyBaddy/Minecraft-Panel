import os
import re
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.config import settings
from app.models.server_event import ServerEvent

class ProcessManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ProcessManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.status = "STOPPED"
            self.process = None
            self.playit_process = None
            self.log_buffer = []
            self.max_log_lines = 2000
            self._log_readers = []
            self._watcher_task = None
            self.session_factory = None
            self.active_players_set = set()
            self._initialized = True

    async def start(self):
        if settings.is_remote_mode:
            self.log_buffer.clear()
            from app.services.console_service import console_service
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(console_service.broadcast_clear())
            except Exception:
                pass
            
            from app.services.agent_coordinator import agent_coordinator
            res = await agent_coordinator.send_request("start_server")
            if res.get("status") == "error":
                raise HTTPException(status_code=400, detail=res.get("detail"))
            return

        if self.status in ("STARTING", "RUNNING"):
            raise HTTPException(status_code=400, detail="Server is already active or starting")

        session_factory = self.session_factory
        if session_factory is None:
            from app.db.session import SessionLocal
            session_factory = SessionLocal

        # Create server directory if missing
        server_dir = os.path.abspath(settings.MINECRAFT_SERVER_DIR)
        os.makedirs(server_dir, exist_ok=True)
        self.active_players_set.clear()

        # Build execution commands
        jar_path = os.path.join(server_dir, settings.MINECRAFT_JAR_NAME)
        # Note: If jar is missing, we create a dummy file for verification to prevent process immediate fail
        if not os.path.exists(jar_path):
            with open(jar_path, "w") as f:
                f.write("# Placeholder for Paper JAR")

        # Command arguments: run start.bat on Windows, fallback to start.sh or direct java on other platforms
        if os.name == "nt":
            bat_path = os.path.join(server_dir, "start.bat")
            if os.path.exists(bat_path):
                cmd = ["cmd.exe", "/c", "start.bat"]
            else:
                cmd = [
                    "java",
                    f"-Xms{settings.MINECRAFT_MIN_RAM}",
                    f"-Xmx{settings.MINECRAFT_MAX_RAM}",
                    "-jar",
                    settings.MINECRAFT_JAR_NAME,
                    "nogui"
                ]
        else:
            sh_path = os.path.join(server_dir, "start.sh")
            if os.path.exists(sh_path):
                cmd = ["/bin/sh", "start.sh"]
            else:
                cmd = [
                    "java",
                    f"-Xms{settings.MINECRAFT_MIN_RAM}",
                    f"-Xmx{settings.MINECRAFT_MAX_RAM}",
                    "-jar",
                    settings.MINECRAFT_JAR_NAME,
                    "nogui"
                ]

        try:
            self.status = "STARTING"
            self.log_buffer.clear()
            from app.services.console_service import console_service
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(console_service.broadcast_clear())
            except Exception:
                pass
            self._append_log("[Panel]: Spawning Minecraft child subprocess...")

            # Run using asyncio subprocess
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=server_dir
            )

            # Check for playit.gg agent — first in server directory, then on system PATH
            playit_bin = "playit.exe" if os.name == "nt" else "playit"
            playit_path = os.path.join(server_dir, playit_bin)
            if not os.path.exists(playit_path):
                # Fall back to system-wide installation (e.g. C:\Program Files\playit_gg\bin\playit.exe)
                import shutil
                system_playit = shutil.which(playit_bin)
                if system_playit:
                    playit_path = system_playit

            if os.path.exists(playit_path):
                self._append_log(f"[Panel]: Found playit.gg agent at {playit_path}. Launching tunnel...")
                try:
                    self.playit_process = await asyncio.create_subprocess_exec(
                        playit_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=server_dir
                    )
                    # Read playit output streams in background tasks
                    asyncio.create_task(self._read_playit_stream(self.playit_process.stdout))
                    asyncio.create_task(self._read_playit_stream(self.playit_process.stderr))
                except Exception as p_err:
                    self._append_log(f"[Panel Warning]: Failed to start playit.gg: {str(p_err)}")

            # Insert Start event in database
            async with session_factory() as db:
                event = ServerEvent(
                    event_type="START",
                    description=f"Server process launched with RAM: {settings.MINECRAFT_MIN_RAM}-{settings.MINECRAFT_MAX_RAM}"
                )
                db.add(event)
                await db.commit()

            # Start stdout/stderr reading and process monitoring
            self._log_readers = [
                asyncio.create_task(self._read_stream(self.process.stdout, "stdout")),
                asyncio.create_task(self._read_stream(self.process.stderr, "stderr"))
            ]
            self._watcher_task = asyncio.create_task(self._process_watcher())

        except Exception as e:
            self.status = "STOPPED"
            self.process = None
            self._append_log(f"[Panel Error]: Failed to spawn subprocess: {str(e)}")
            raise e

    async def stop(self):
        if settings.is_remote_mode:
            from app.services.agent_coordinator import agent_coordinator
            res = await agent_coordinator.send_request("stop_server")
            if res.get("status") == "error":
                raise HTTPException(status_code=400, detail=res.get("detail"))
            return

        if not self.process or self.status == "STOPPED":
            raise HTTPException(status_code=400, detail="Server is not running")

        self.status = "STOPPING"
        self._append_log("[Panel]: Sending graceful stop command to stdin...")
        await self.write_stdin("stop")

        # Wait for normal exit
        for _ in range(30): # 30 seconds timeout
            if self.process is None or self.status == "STOPPED":
                return
            await asyncio.sleep(1)

        # Force kill if still running after timeout
        if self.process:
            self._append_log("[Panel Warning]: Graceful stop timed out. Sending SIGKILL...")
            await self.kill()

    async def kill(self):
        if settings.is_remote_mode:
            from app.services.agent_coordinator import agent_coordinator
            await agent_coordinator.send_request("kill_server")
            return

        if not self.process:
            return
        
        session_factory = self.session_factory
        if session_factory is None:
            from app.db.session import SessionLocal
            session_factory = SessionLocal
        
        try:
            self.process.kill()
            self._append_log("[Panel]: Subprocess terminated via SIGKILL.")
        except ProcessLookupError:
            pass
        finally:
            if self.playit_process:
                try:
                    self.playit_process.kill()
                except Exception:
                    pass
                self.playit_process = None
            self.status = "STOPPED"
            self.process = None
            
            # Log kill event to database
            async with session_factory() as db:
                event = ServerEvent(
                    event_type="SIGKILL",
                    description="Server process forcefully killed after shutdown timeout"
                )
                db.add(event)
                await db.commit()

    async def write_stdin(self, command: str):
        if settings.is_remote_mode:
            from app.services.agent_coordinator import agent_coordinator
            await agent_coordinator.send_request("write_stdin", {"command": command})
            return

        if not self.process or not self.process.stdin:
            return
        
        # Strip trailing newlines and inject standard carriage return
        cmd_bytes = (command.strip() + "\n").encode("utf-8")
        self.process.stdin.write(cmd_bytes)
        await self.process.stdin.drain()

    async def _read_stream(self, stream, stream_name: str):
        import codecs
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        buffer = ""
        while True:
            try:
                # Read chunks of bytes to avoid blocking on prompts that do not end with newlines (e.g. pause statement)
                chunk_bytes = await stream.read(1024)
                if not chunk_bytes:
                    buffer += decoder.decode(b"", final=True)
                    if buffer:
                        self._process_log_line(buffer, stream_name)
                    break
                
                buffer += decoder.decode(chunk_bytes, final=False)
                
                # Extract and process complete lines
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self._process_log_line(line, stream_name)
                
                # Check for prompt like "Press any key to continue" in the current buffer (without waiting for a newline)
                if "Press any key to continue" in buffer:
                    self._process_log_line(buffer, stream_name)
                    buffer = ""
                    await self.write_stdin("")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._append_log(f"[Panel Error] Error reading {stream_name}: {str(e)}")
                break

    def _process_log_line(self, line: str, stream_name: str):
        line = line.strip()
        if not line:
            return
        
        self._append_log(line)
        
        # Transition Starting -> Running upon console boot indicators
        if self.status == "STARTING" and ("Done (" in line or "For help, type" in line):
            self.status = "RUNNING"
            self._append_log("[Panel]: Server boot detected. Status changed to RUNNING.")
        
        # Parse player joins/leaves
        if " joined the game" in line:
            idx = line.find(" joined the game")
            colon = line.rfind("]: ", 0, idx)
            if colon != -1:
                username = line[colon + 3:idx].strip()
            else:
                username = line[:idx].strip()
                if " " in username:
                    username = username.split()[-1]
            
            # Remove ANSI color/formatting codes
            username = re.sub(r'\x1B\s*(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', username)
            username = username.strip()
            if username:
                self.active_players_set.add(username)
                    
        elif " left the game" in line:
            idx = line.find(" left the game")
            colon = line.rfind("]: ", 0, idx)
            if colon != -1:
                username = line[colon + 3:idx].strip()
            else:
                username = line[:idx].strip()
                if " " in username:
                    username = username.split()[-1]
            
            # Remove ANSI color/formatting codes
            username = re.sub(r'\x1B\s*(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', username)
            username = username.strip()
            if username:
                self.active_players_set.discard(username)

    async def _process_watcher(self):
        if not self.process:
            return

        session_factory = self.session_factory
        if session_factory is None:
            from app.db.session import SessionLocal
            session_factory = SessionLocal

        exit_code = await self.process.wait()
        
        # Clean up playit process if running
        if self.playit_process:
            self._append_log("[Panel]: Subprocess exited. Cleaning up playit.gg tunnel...")
            try:
                self.playit_process.kill()
                await self.playit_process.wait()
            except Exception:
                pass
            self.playit_process = None

        # Clean up stream readers
        for reader in self._log_readers:
            if not reader.done():
                reader.cancel()
        self.active_players_set.clear()
        
        self.process = None
        old_status = self.status
        self.status = "STOPPED"
        self._append_log(f"[Panel]: Subprocess exited with code {exit_code}")

        # Log event to database
        async with session_factory() as db:
            if old_status == "STOPPING" or exit_code == 0:
                event = ServerEvent(
                    event_type="STOP",
                    description="Server process stopped gracefully",
                    exit_code=exit_code
                )
            else:
                self.status = "CRASHED"
                event = ServerEvent(
                    event_type="CRASH",
                    description=f"Server process terminated unexpectedly with exit code {exit_code}",
                    exit_code=exit_code
                )
            db.add(event)
            await db.commit()

    def _append_log(self, line: str):
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        formatted_line = f"[{timestamp} INFO]: {line}"
        self.log_buffer.append(formatted_line)
        if len(self.log_buffer) > self.max_log_lines:
            self.log_buffer.pop(0)

        # Broadcast line to connected console WebSocket subscribers
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                from app.services.console_service import console_service
                loop.create_task(console_service.broadcast(formatted_line))
        except RuntimeError:
            pass

    def _append_log_direct(self, line: str):
        self.log_buffer.append(line)
        if len(self.log_buffer) > self.max_log_lines:
            self.log_buffer.pop(0)

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                from app.services.console_service import console_service
                loop.create_task(console_service.broadcast(line))
        except RuntimeError:
            pass

    async def _read_playit_stream(self, stream):
        try:
            while True:
                line_bytes = await stream.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode('utf-8', errors='replace').strip()
                if line:
                    # Print clean playit tunnel logs directly in panel console
                    self._append_log(f"[playit.gg]: {line}")
        except Exception:
            pass

# Instantiate singleton process manager
process_manager = ProcessManager()

class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
