# Application Flow and Diagrams (AppFlow)

## 1. Authentication Flow
The sequence diagram below shows how a user authenticates with the frontend, receives a secure HttpOnly JWT cookie, and accesses protected endpoints.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as React Frontend
    participant BE as FastAPI API Layer
    participant AS as AuthService
    participant DB as SQLite Database

    User->>FE: Input credentials & submit
    FE->>BE: POST /api/auth/login (JSON credentials)
    BE->>AS: authenticate_user(username, password)
    AS->>DB: Fetch user by username
    DB-->>AS: User record (with password hash)
    AS->>AS: Verify password hash (Argon2id)
    alt Credentials Invalid
        AS-->>BE: Raise InvalidCredentialsException
        BE-->>FE: HTTP 401 Unauthorized
        FE-->>User: Show authentication error
    else Credentials Valid
        AS->>AS: Generate JWT Token (roles, expiry)
        AS-->>BE: JWT Token string
        BE-->>FE: HTTP 200 OK + Cookie (HttpOnly, Secure, SameSite=Strict)
        FE->>FE: Update AuthContext state
        FE->>User: Redirect to Dashboard
    end
```

---

## 2. Server Lifecycle State Machine
The Minecraft server process transitions through specific states based on administrator action or operating system feedback. The panel uses a cascading launch strategy: on Windows, it first attempts `start.bat`, then falls back to direct `java -jar` execution. During transitions, synthesized 8-bit sound chimes are played in the browser.

```mermaid
stateDiagram-v2
    [*] --> STOPPED
    
    STOPPED --> STARTING : User clicks "Start" / API triggers launch
    
    STARTING --> RUNNING : Log parser detects "Done" (Plays Start Chime)
    STARTING --> CRASHED : Process exits with code != 0 before "Done" (Plays Stop Chime)
    STARTING --> STOPPED : Process exits with code == 0 before "Done" (Plays Stop Chime)
    
    RUNNING --> STOPPING : User clicks "Stop" / Graceful shutdown
    RUNNING --> RESTARTING : User clicks "Restart" (Sets isRestarting=true)
    RUNNING --> CRASHED : Process terminates unexpectedly (Plays Stop Chime)
    RUNNING --> STOPPED : Process terminates with exit code 0 (Plays Stop Chime)
    
    STOPPING --> STOPPED : Process exits cleanly (Plays Stop Chime)
    STOPPING --> CRASHED : Process is SIGKILL'd after timeout (Plays Stop Chime)

    RESTARTING --> STARTING : Process exits and immediate reboot starts
    STARTING --> RUNNING_RESTART : Log parser detects "Done" inside restart cycle
    RUNNING_RESTART --> RUNNING : isRestarting sets to false (Plays Restart Chime)
```

---

## 3. Server Lifecycle Management Flow
Below is the sequence for starting or gracefully stopping the Minecraft server process.

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant FE as React Frontend
    participant BE as FastAPI API Layer
    participant PM as ProcessManager Service
    participant Proc as Java Subprocess
    
    Note over Admin, Proc: Server Start Sequence
    Admin->>FE: Click "Start Server"
    FE->>BE: POST /api/server/lifecycle (action="start") [With JWT Cookie]
    BE->>PM: start_server()
    alt Server already running
        PM-->>BE: Raise ProcessAlreadyRunningException
        BE-->>FE: HTTP 400 Bad Request
        FE-->>Admin: Show error toast
    else Server stopped
        PM->>PM: Create Java execution command
        PM->>Proc: Spawn Subprocess (java -jar paper.jar)
        PM->>PM: Register Async Log Reader Loop
        PM-->>BE: Return status: "STARTING"
        BE-->>FE: HTTP 200 OK (status="STARTING")
        FE-->>Admin: UI updates to STARTING state
    end

    Note over Admin, Proc: Log Reader Loop detects running status
    Proc->>PM: Stdout line: "[Server thread/INFO]: Done (12.4s)!"
    PM->>PM: Update state to "RUNNING"
    PM-->>FE: WebSocket broadcast: {"event": "status_change", "status": "RUNNING"}
    FE-->>Admin: UI updates to RUNNING state

    Note over Admin, Proc: Server Stop Sequence
    Admin->>FE: Click "Stop Server"
    FE->>BE: POST /api/server/lifecycle (action="stop") [With JWT Cookie]
    BE->>PM: stop_server()
    PM->>Proc: Write "stop\n" to stdin (graceful stop command)
    PM->>PM: Wait for subprocess exit status (timeout 30s)
    alt Graceful Exit
        Proc-->>PM: Subprocess exits (exit code 0)
        PM->>PM: Update state to "STOPPED"
        PM-->>FE: WebSocket broadcast: {"event": "status_change", "status": "STOPPED"}
        FE-->>Admin: UI updates to STOPPED state
    else Process Hangs (Timeout Exceeded)
        PM->>Proc: Send kill signal (SIGKILL)
        Proc-->>PM: Subprocess terminates
        PM->>PM: Update state to "CRASHED"
        PM-->>FE: WebSocket broadcast: {"event": "status_change", "status": "CRASHED"}
        FE-->>Admin: UI updates to CRASHED state
    end
```

---

## 4. Console Management & Command Execution Flow
This diagram details how the panel streams log outputs via WebSocket to active clients and handles console input.

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant FE as React Frontend
    participant WS as WebSocket Connection
    participant BE as FastAPI WebSocket Handler
    participant PM as ProcessManager Service
    participant AL as AuditLogService

    Note over FE, PM: WebSocket Console Streaming Loop
    Admin->>FE: Open Console Page
    FE->>WS: Connect to ws://host/api/console/stream
    WS->>BE: Upgrade HTTP Connection
    BE->>PM: Register client session
    PM-->>WS: Emit recent console history (last 100 lines)
    WS-->>FE: Load history in Terminal window
    
    loop Stream Output
        PM->>PM: Read line from Java subprocess stdout
        PM->>BE: Push line to broadcast queue
        BE->>WS: Send frame: {"log": "[19:07:46 INFO]: User joined"}
        WS->>FE: Render line in terminal
    end

    Note over Admin, AL: Command Execution Flow
    Admin->>FE: Type command "op Alex" and hit Enter
    FE->>BE: POST /api/console/command {"command": "op Alex"}
    BE->>BE: Authenticate user & check permission (Admin/Mod)
    alt Permission Denied
        BE-->>FE: HTTP 403 Forbidden
        FE-->>Admin: Show "Access Denied" toast
    else Permission Approved
        BE->>AL: log_action(user_id, "EXECUTE_COMMAND", "op Alex")
        AL->>BE: Audit log saved
        BE->>PM: write_to_stdin("op Alex\n")
        PM->>PM: Write "op Alex\n" to subprocess stdin pipe
        BE-->>FE: HTTP 200 OK (command received)
    end
```

---

## 4.5 Player Join/Disconnect Telemetry & Chime Flow
This diagram details how the backend parses player events from the server stream, extends metrics telemetry, and triggers chimes and toast alerts on the React frontend.

```mermaid
sequenceDiagram
    autonumber
    actor Player
    participant Server as Minecraft Server Subprocess
    participant PM as ProcessManager Service
    participant Metrics as MetricsService
    participant FE as React Frontend

    Player->>Server: Connects / Joins Game
    Server->>PM: Stream line: "[12:01:23] [Server thread/INFO]: Alex joined the game"
    PM->>PM: Parse line, extract username "Alex", add to active_players_set
    loop Telemetry broadcast (every 2 seconds)
        Metrics->>PM: Read active_players_set & size
        PM-->>Metrics: return count and list of player names
        Metrics->>FE: WebSocket push: {"active_players": 1, "active_players_list": ["Alex"], ...}
        FE->>FE: Compare current list with prevPlayersListRef.current
        FE->>FE: Detect "Alex" joined
        FE-->>FE: Show Toast: "Alex joined the game"
        FE-->>FE: Play synthesized Player Join Chime (E5 -> A5)
    end
```

---

## 4.6 Playit.gg Tunnel Auto-Detection Flow
This diagram details how the panel detects and manages the playit.gg tunnel agent alongside the Minecraft server process.

```mermaid
sequenceDiagram
    autonumber
    participant PM as ProcessManager Service
    participant Proc as Minecraft Server Subprocess
    participant PlayIt as Playit.gg Tunnel Subprocess
    participant FE as React Frontend

    Note over PM, PlayIt: Server Start with Tunnel Detection
    PM->>Proc: Spawn Minecraft Server (start.bat or java -jar)
    PM->>PM: Check for playit.exe/playit in server directory
    alt Playit binary found
        PM->>PlayIt: Spawn playit.exe as async subprocess
        PM->>PM: Register stdout/stderr readers for tunnel
        PM-->>FE: Console log: "[Panel]: Found playit.gg agent. Launching tunnel..."
        loop Stream Tunnel Output
            PlayIt->>PM: stdout line: tunnel status/address info
            PM-->>FE: Console log: "[playit.gg]: <tunnel output>"
        end
    else Playit binary not found
        PM-->>FE: No tunnel detection (silent skip)
    end

    Note over PM, PlayIt: Server Stop with Tunnel Cleanup
    PM->>Proc: Send stop command to Minecraft stdin
    Proc-->>PM: Subprocess exits
    alt Playit process running
        PM->>PlayIt: Kill tunnel subprocess
        PlayIt-->>PM: Tunnel process terminated
        PM-->>FE: Console log: "[Panel]: Cleaning up playit.gg tunnel..."
    end
    PM->>PM: Update state to STOPPED
```

---

## 5. Backup Flow
Manual backup generation requires stopping disk activity temporarily to avoid copying corrupted files.

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant FE as React Frontend
    participant BE as FastAPI API Layer
    participant BS as BackupService
    participant PM as ProcessManager Service
    participant Repo as BackupRepository
    
    Admin->>FE: Click "Create Backup"
    FE->>BE: POST /api/backups/create [With JWT Cookie]
    BE->>BE: Verify Admin permissions
    BE->>BS: create_backup()
    BS->>PM: get_status()
    alt Server is RUNNING
        BS->>PM: write_to_stdin("save-off\n")
        BS->>PM: write_to_stdin("save-all\n")
        Note over BS, PM: Pauses world writes and flushes buffer to disk
    end
    BS->>BS: Zip world & config folders (exclude logs, cache)
    alt Server was RUNNING
        BS->>PM: write_to_stdin("save-on\n")
        Note over BS, PM: Resumes world writing
    end
    BS->>Repo: Create database record (file size, location, checksum)
    Repo-->>BS: Record created
    BS-->>BE: Return backup metadata
    BE-->>FE: HTTP 201 Created (backup details)
    FE-->>Admin: Display success notification
```

---

## 6. Restore Flow
Restoring a backup completely overwrites active server files and requires a process shutdown.

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant FE as React Frontend
    participant BE as FastAPI API Layer
    participant BS as BackupService
    participant PM as ProcessManager Service
    
    Admin->>FE: Click "Restore" on Backup #12
    FE->>BE: POST /api/backups/12/restore [With JWT Cookie]
    BE->>BE: Verify Admin permissions
    BE->>BS: restore_backup(backup_id=12)
    BS->>PM: stop_server()
    Note over BS, PM: Ensure process is fully shut down before restoration
    PM-->>BS: Confirmation process is stopped
    BS->>BS: Move current world directories to temp location
    BS->>BS: Extract Backup #12 archive files to server directory
    alt Extraction successful
        BS->>BS: Delete temporary location
        BS->>PM: start_server()
        BS-->>BE: Return success
        BE-->>FE: HTTP 200 OK
        FE-->>Admin: Show success toast, status transitions to STARTING
    else Extraction failed
        BS->>BS: Restore world files from temporary folder (Rollback)
        BS->>PM: start_server()
        BS-->>BE: Raise BackupRestorationException
        BE-->>FE: HTTP 500 Internal Server Error
        FE-->>Admin: Show restore failure alert
    end
```

---

## 7. Configuration Management Flow
This sequence shows the path validation logic enforced when retrieving or modifying settings.

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant FE as React Frontend
    participant BE as FastAPI API Layer
    participant CS as ConfigService
    
    Note over Developer, CS: Fetch Configuration File
    Developer->>FE: Select "server.properties" in Editor
    FE->>BE: GET /api/config/settings?file=server.properties
    BE->>CS: read_config("server.properties")
    CS->>CS: Resolve path & verify sandbox boundaries
    alt Out of bounds path
        CS-->>BE: Raise PathTraversalException
        BE-->>FE: HTTP 403 Forbidden (Access Denied)
    else Sandbox safe path
        CS->>CS: Parse properties file into JSON schema
        CS-->>BE: Return configuration JSON object
        BE-->>FE: HTTP 200 OK (JSON configuration data)
        FE-->>Developer: Render configuration in form/editor
    end

    Note over Developer, CS: Save Modified Settings
    Developer->>FE: Edit setting (e.g. max-players: "abc" -> "20") & click Save
    FE->>BE: POST /api/config/settings?file=server.properties (JSON payload)
    BE->>BE: Verify Admin Role
    BE->>CS: write_config("server.properties", json_data)
    CS->>CS: Run structural & data type validations
    alt Data Validation Failed (e.g. type mismatch)
        CS-->>BE: Raise ConfigurationValidationException
        BE-->>FE: HTTP 422 Unprocessable Entity
        FE-->>Developer: Highlight input field validation error
    else Validation Passed
        CS->>CS: Convert JSON payload back to .properties format
        CS->>CS: Write contents to disk (temp file then rename)
        CS-->>BE: Return write confirmation
        BE-->>FE: HTTP 200 OK
        FE-->>Developer: Show settings saved toast
    end
```

---

## 8. WebSocket Reconnection and Error Flow
Handles recovery from unexpected communication drops.

```mermaid
stateDiagram-v2
    [*] --> CONNECTED
    
    CONNECTED --> DISCONNECTED : Network drops / Server restarted
    
    DISCONNECTED --> RECONNECTING_ATTEMPT_1 : Trigger recon loop after 1s
    
    RECONNECTING_ATTEMPT_1 --> CONNECTED : Connection restored
    RECONNECTING_ATTEMPT_1 --> RECONNECTING_ATTEMPT_2 : Fails / Wait 2s (exponential)
    
    RECONNECTING_ATTEMPT_2 --> CONNECTED : Connection restored
    RECONNECTING_ATTEMPT_2 --> RECONNECTING_ATTEMPT_3 : Fails / Wait 4s
    
    RECONNECTING_ATTEMPT_3 --> CONNECTED : Connection restored
    RECONNECTING_ATTEMPT_3 --> CONNECTION_LOST_BANNER : Fails / Wait 8s / Stop auto-reconnect
    
    CONNECTION_LOST_BANNER --> CONNECTED : User clicks "Manual Reconnect" & succeeds
    CONNECTION_LOST_BANNER --> [*] : User leaves page
```
