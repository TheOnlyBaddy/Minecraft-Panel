# Technical Specification (TechSpec)

## 1. System Architecture & High-Level Design
The Antigravity Panel is designed as a **Modular Monolith** to keep deployment simple while maintaining strict boundaries between logical domains. The architecture separation ensures that concerns such as UI rendering, API routing, business logic, data access, and OS process wrapper logic are decoupled.

### System Components Diagram
```
+-----------------------------------------------------------+
|                      React Web UI                         |
|   (Dashboard, Terminal Console, Config Editor, Backups)   |
+-----------------------------+-----------------------------+
                              | HTTPS / WebSockets
                              v
+-----------------------------------------------------------+
|                    FastAPI Backend                        |
|                                                           |
|  +-----------------------------------------------------+  |
|  |                     API Layer                       |  |
|  |  (REST Endpoints, WebSocket Protocol Handlers)     |  |
|  +--------------------------+--------------------------+  |
|                             |                             |
|  +--------------------------v--------------------------+  |
|  |                   Service Layer                     |  |
|  |  (AuthService, ProcessManager, ConfigService,       |  |
|  |   BackupService, MetricsService, AuditLogService)   |  |
|  +--------------------------+--------------------------+  |
|                             |                             |
|  +--------------------------v--------------------------+  |
|  |                  Repository Layer                   |  |
|  |  (UserRepository, BackupRepository, AuditLogRepo)   |  |
|  +--------------------------+--------------------------+  |
+-----------------------------+-----------------------------+
                              |
              +---------------+---------------+
              |                               |
              v SQLite                        v OS File System & Process Control
+-----------------------------+ +-----------------------------+
|    Database (sqlite3)       | |   Minecraft Server Jar      |
|                             | |  (Subprocess stdout/stdin)  |
+-----------------------------+ +-----------------------------+
```

---

## 2. Technology Stack

### Backend
* **Language**: Python 3.10+
* **Web Framework**: FastAPI (high-performance ASGI framework)
* **ASGI Server**: Uvicorn
* **Database Access**: SQLAlchemy (ORM & Core) or raw `sqlite3` using async drivers. For ease of migration to PostgreSQL, SQLAlchemy with asyncpg/aiosqlite is selected.
* **Process Utilities**: `psutil` (for system and process-specific resource metrics)
* **Security**: `passlib[bcrypt]` (for password hashing), `PyJWT` (for JWT administration or secure cookies)

### Frontend
* **Framework**: React 18+ (Vite-powered build toolchain)
* **Language**: TypeScript (strict mode)
* **Styling**: Tailwind CSS (v4.x) with PostCSS pipeline for rapid design iterations and centralized utility-first styling token overrides
* **Icons**: Lucide React
* **Terminal UI**: Custom-built interactive shell scroll window with monospace logs, auto-scroll locks, and a slash command autocomplete suggestion menu (triggered by `/`)
* **Audio Engine**: Synthesized 8-bit sound effects (chimes) generated in real-time in the browser using the Web Audio API
* **Mobile Responsive Layout**: Sidebar drawer with hamburger toggle, touch-dismiss backdrop, and card-based table fallbacks for viewports under 768px
* **Dynamic Branding**: Runtime logo/background detection via HEAD preload with emerald shield and deepslate tile fallbacks

### Realtime Communication
* **WebSockets**: Standard WebSocket protocol supported by FastAPI and native browser WebSocket API. Used for:
  1. Live log streaming (stdout/stderr).
  2. Real-time resource metrics (CPU, RAM, Disk, active player count, and active players list).
  3. Minecraft server state transitions.

### Data Storage
* **SQLite** (`dev.db` or `production.db` local file). SQLite is configured in Write-Ahead Logging (WAL) mode to permit concurrent reads and avoid locking during background metrics logging and audit log inserts.

---

## 3. Backend Architecture

### Directory Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application bootstrap & FastAPI routes setup
│   ├── config.py               # Panel configuration (environment variables)
│   ├── api/                    # API Routing Layer
│   │   ├── deps.py             # Dependency injection definitions (DB, Auth)
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── server.py           # Lifecycle & process commands
│   │   ├── console.py          # WebSocket log stream & input commands
│   │   ├── config_mgmt.py      # Configuration reading/writing
│   │   ├── backups.py          # Backup control endpoints
│   │   └── audit.py            # Audit log viewer endpoints
│   ├── core/                   # Cross-cutting concerns
│   │   ├── security.py         # Password hashing and token utilities
│   │   └── exceptions.py       # Custom exceptions and exception handlers
│   ├── db/                     # Database setup
│   │   ├── base.py             # Base model definition
│   │   └── session.py          # Engine and session creation
│   ├── models/                 # Database entity models
│   │   ├── user.py
│   │   ├── audit_log.py
│   │   ├── backup.py
│   │   └── metric.py
│   ├── repositories/           # Repository Layer
│   │   ├── base.py
│   │   ├── user_repo.py
│   │   ├── audit_repo.py
│   │   └── backup_repo.py
│   └── services/               # Service Layer
│       ├── process_manager.py  # Subprocess wrapper, stdin/stdout handlers
│       ├── auth_service.py     # Login, tokens, verification
│       ├── config_service.py   # Properties file parser & writer
│       ├── backup_service.py   # Archiving and restoration execution
│       ├── metrics_service.py  # Background system resource collector
│       └── audit_service.py    # Log event generator
└── tests/                      # Pytest suite
```

### Dependency Injection
FastAPI's dependency injection system (`Depends`) is utilized to supply repositories, database sessions, configurations, and authenticated users to the route controllers. This ensures modularity and supports mocking during unit and integration testing.

---

## 4. Frontend Architecture

### Module Organization
```
frontend/
├── public/                    # Static assets (background.png, logo.png)
├── src/
│   ├── components/             # Reusable UI Components
│   │   ├── LoadingScreen.tsx  # Retro XP-bar loading with dynamic branding
│   │   ├── Logo.tsx           # Dynamic logo with /logo.png detection & shield fallback
│   │   └── StatusBadge/
│   ├── context/                # Global contexts (AuthContext, ToastContext)
│   ├── hooks/                  # Custom hooks (useWebSocket, useConsoleWebSocket)
│   ├── pages/                  # Top-level Page Views
│   │   ├── Login/              # Login screen with animated panorama/panning backdrop
│   │   └── Dashboard/          # Dashboard wrapper with collapsible sidebar / mobile drawer
│   │       └── tabs/           # Modular View Tabs (Server, Console, Options, Access)
│   ├── utils/                  # Telemetry utilities, synthesized 8-bit audio module (audio.ts)
│   ├── App.tsx                 # Main routing and provider hierarchy
│   ├── main.tsx                # DOM entry point
│   └── index.css               # Global CSS variables, GPU keyframe animations & responsive breakpoints
```

### State Management
* **Authentication**: Managed via React Context API (`AuthContext`), storing the token in a secure HttpOnly cookie or session storage, alongside the user metadata.
* **Server Telemetry & Metrics**: Stored within local page/hook state and updated via active WebSocket connections. When pages unmount, WebSockets are disconnected to prevent connection leaks.
* **Console Logs**: Kept in a ring buffer (maximum 2,000 lines) within the custom terminal component to prevent browser memory exhaustion.

---

## 5. Authentication & Authorization Design

### Authentication Protocol
1. **Flow**: Token-based authentication using **JSON Web Tokens (JWT)** or **Secure Session Tokens** stored in a secure cookie. Cookies are configured with the following flags:
   * `HttpOnly = True` (prevents XSS retrieval)
   * `Secure = True` (requires HTTPS transmission)
   * `SameSite = Strict` (mitigates CSRF vulnerabilities)
2. **Algorithm**: HMAC-SHA256 for signing tokens, using a secure environment-provided `SECRET_KEY`.
3. **Password Security**: Argon2id (via passlib) with a minimum memory cost of 65,536 KB, time cost of 3 iterations, and parallelism of 4.

### Authorization Model (RBAC)
Two primary system roles are enforced:
* `ROLE_ADMIN`: Full capabilities, including system configuration, database operations, user management, and backup restorations.
* `ROLE_MODERATOR`: Read-only views of settings, resource statistics, logs, and authorization to issue commands via the console. Prohibited from executing backups, changing configs, or modifying users.

| Operation | Route | Admin | Moderator |
|---|---|---|---|
| Read Telemetry | WS `/api/server/telemetry` | Yes | Yes |
| Start/Stop/Restart | POST `/api/server/lifecycle` | Yes | Yes |
| Read Live Console | WS `/api/server/console/stream` | Yes | Yes |
| Send Console Cmd | POST `/api/server/console/command` | Yes | Yes |
| Read Properties | GET `/api/server/config` | Yes | Yes |
| Edit Properties | POST `/api/server/config/save` | Yes | No |
| Create Backup | POST `/api/backups/create` | Yes | Yes |
| Restore Backup | POST `/api/backups/restore/{id}` | Yes | No |
| Delete Backup | DELETE `/api/backups/{id}` | Yes | No |
| Read Audit Logs | GET `/api/audit` | Yes | No |

---

## 6. Service Layer Design

### Process Manager Service (`ProcessManager`)
Responsible for wrapping the Minecraft Paper Java execution and managing auxiliary tunnel agents.
* Implements a **flexible launch strategy**:
  * On Windows, checks for `start.bat` in the server directory and runs it via `cmd.exe /c start.bat` if found.
  * If no batch script exists, falls back to direct Java execution:
    ```python
    cmd = ["java", f"-Xms{ram_min}", f"-Xmx{ram_max}", "-jar", "paper.jar", "nogui"]
    ```
  * On Linux, checks for `start.sh` before falling back to direct Java.
* Runs the subprocess using Python `subprocess.Popen` / `asyncio.create_subprocess_exec` with argument lists (not raw shell strings):
  ```python
  process = await asyncio.create_subprocess_exec(
      *cmd,
      stdin=asyncio.subprocess.PIPE,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
      cwd=server_dir,
  )
  ```
* **Playit.gg Tunnel Auto-Detection**: After launching the server, checks for `playit.exe` (Windows) or `playit` (Linux) in the server directory. If found, spawns it as a separate async subprocess, streams its output with `[playit.gg]:` prefix into the panel console, and terminates it automatically when the server stops.
* Spawn async background tasks to read `stdout` and `stderr` continuously without blocking the main event loop.
* Distribute log lines to active WebSocket connections via an in-memory broadcast manager (Pub/Sub pattern).
* Parse player join/disconnect events from log lines to maintain an `active_players_set` for telemetry.
* Write log entries to a local log buffer/file on disk for console history retrievals.

### Backup Service (`BackupService`)
Coordinates backup operations.
* **Creation**:
  1. Send `/save-off` and `/save-all` commands to the Minecraft stdin to pause world writing and flush data to disk.
  2. Create a zip/tar archive of the world directories, excluding cache folders (e.g., `cache/`, `logs/`, `.git/`).
  3. Send `/save-on` command to resume world writing.
  4. Write a record to the Backup database repository.
* **Restoration**:
  1. Terminate the Minecraft process safely.
  2. Clean the target directories (backup the current folder to a temp directory to prevent fatal errors).
  3. Extract the backup archive.
  4. Restart the Minecraft process.

### Metrics Service (`MetricsService`)
* Runs a periodic background thread (every 2 seconds when WebSocket clients are connected, otherwise every 60 seconds for historical logs).
* Employs `psutil` to retrieve system-wide metrics (CPU percentage, memory used/total, disk IO, disk usage) and process-specific metrics (Minecraft Java process memory, CPU utilization, thread count).
* Pushes metrics dynamically to the frontend dashboard via the WebSocket manager.

---

## 7. Repository Layer Design
The Repository Layer abstracts the database calls, implementing standard CRUD operations on database models.

### Base Repository Structure
Repositories inherit from a generic base repository class implementing:
* `get(id)`
* `get_multi(skip, limit)`
* `create(obj_in)`
* `update(db_obj, obj_in)`
* `delete(id)`

This separation ensures that SQLite-specific queries can be adapted to PostgreSQL dialects seamlessly by modifying only the database schemas and dialect settings in the SQLAlchemy layer.

---

## 8. Logging & Observability Strategy

### Structured Logging
* The application uses standard Python `logging` customized to output structured JSON format in production.
* Log structure:
  ```json
  {
    "timestamp": "2026-06-12T19:07:46Z",
    "level": "INFO",
    "module": "services.process_manager",
    "message": "Minecraft server subprocess successfully spawned",
    "process_id": 14208,
    "user_id": null
  }
  ```
* Logger outputs to standard output (`stdout`) for container engines or log collection systems, and is duplicated to a daily rotating file logger (`/logs/panel.log`) with a 10MB retention cap and 7-day backup index.

### Audit Logging
Audit logging tracks user operations. Audit logs are written directly to the database in a transactional block. Every action that modifies system state (starting/stopping server, restoring backup, writing config, editing credentials) *must* call the `AuditLogService` inside its execution path.

---

## 9. Security Design

### Prevention of Arbitrary Execution
To eliminate any vector for command injection or remote code execution (RCE) on the host machine:
* **Shell Disabled**: `shell=False` is set on every subprocess execution.
* **Argument Sanitization**: Arguments passed to `subprocess.Popen` are strictly program arguments, never parsed through a shell interpreter.
* **Command Safelist**: Commands sent to the Minecraft console are checked against a character pattern `^[a-zA-Z0-9\s_\-\/\?\!\:]+$` and truncated to a maximum of 256 characters. This prevents injecting carriage returns or escape characters.
* **Directory Sandboxing**: The Backup Service and Configuration Service validate all paths using `os.path.commonpath`. Attempting to read, edit, or write a file outside the designated Minecraft server directory returns a strict authorization error, preventing path traversal attacks (e.g., `../../etc/passwd`).

---

## 10. Tradeoff Analysis

### SQLite vs. PostgreSQL
* **Selected**: SQLite (initial version).
* **Rationale**: Simplicity. A Minecraft management panel runs on the same machine as the game server. Requiring a separate PostgreSQL service complicates installation. Utilizing SQLite in WAL mode provides sufficient write/read concurrency for single-server setups. The database layer is decoupled using SQLAlchemy, enabling simple migration to PostgreSQL (Phase D) if multi-server operations require centralized data storage.

### Subprocess Wrapper vs. Docker Containers
* **Selected**: Subprocess Wrapper.
* **Rationale**: Direct compatibility with existing local setups. Spawning Java via subprocess allows admins to run the panel on bare metal or custom VMs without configuring Docker sockets and storage mappings.
* **Consequence**: The panel process requires system-level privileges equivalent to the Minecraft execution user. Isolation must be managed using system users (e.g., creating a dedicated `minecraft` user group).

### WebSockets vs. SSE (Server-Sent Events) + REST
* **Selected**: WebSockets.
* **Rationale**: True bi-directional streaming is required for interactive console commands. Using SSE for logs and REST for inputs is a viable alternative, but WebSockets provide lower latency and a single connection abstraction for both telemetry updates, output logs, and user terminal commands.
