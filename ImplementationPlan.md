# Implementation Plan (ImplementationPlan)

## Phase 0: Project Setup
Setting up code repositories, linters, base packages, folder structure, and database connection hooks.

### Objectives
* Establish backend and frontend environment structures.
* Configure database migrations and initial schema setup.
* Configure static code analysis, formatting rules, and development servers.

### Deliverables
* Integrated Git repository with `.gitignore` configurations.
* Poetry or requirements.txt setup for Python packages.
* Vite React TypeScript project setup in the `frontend/` directory.
* SQLite database initialization scripts with WAL configuration.

### Tasks
1. Initialize a git repository with standard exclusions for Python, node_modules, and Java runtime cache.
2. Initialize backend directory with FastAPI, Uvicorn, SQLAlchemy, Alembic, and pytest dependencies.
3. Configure `database.py` session logic and run base Alembic setup.
4. Initialize the frontend module via Vite with TypeScript compiler settings.
5. Configure Tailwind CSS directives and custom theme global variables in `index.css`.
6. Establish dummy landing pages for frontend and default root router for backend.

### Dependencies
* None.

### Risks
* SQLite database file path conflicts in local environments. (Mitigation: Use environment variables for the database URI).

### Definition of Done
* `npm run dev` and `uvicorn main:app --reload` run successfully concurrently.
* Pytest executes and passes a simple health check test.
* Database initialization generates `dev.db` with 100% correct empty tables matching Schema.md.

---

## Phase 1: Authentication & Authorization
Establishing authentication middleware, RBAC checks, and secure user sessions.

### Objectives
* Enable login and logout endpoints.
* Establish secure JWT token cookies.
* Implement user database models and default administrator seed.

### Deliverables
* Working `/api/auth/login` and `/api/auth/logout` API routes.
* Authentication and Role-Verification guards in FastAPI (Depends).
* Frontend Auth Context (`AuthContext`) and Auth layout page.

### Tasks
1. Write the SQLAlchemy data models for `User` and `Session`.
2. Write password hashing utilities using `passlib[bcrypt]`.
3. Implement `AuthService` logic for credential validation and token generation.
4. Implement FastAPI dependency injectables: `get_current_user` and `check_role`.
5. Develop frontend Login page using Vanilla CSS modules.
6. Connect frontend Axios/fetch client to handle authentication headers and cookies.
7. Build simple user management interface for creating junior moderators.

### Dependencies
* Phase 0 completed.

### Risks
* Exposing authentication tokens via Cross-Site Scripting (XSS). (Mitigation: Use strictly HttpOnly, Secure, SameSite=Strict cookies for token delivery).

### Definition of Done
* Attempting to access dashboard routes redirects unauthenticated users to `/login`.
* Moderator login restricts access to setting edits and backup restoration.
* Passwords are saved in database strictly as Argon2id/bcrypt hashes.

---

## Phase 2: Server Process Management
Spawning the Minecraft Java process, monitoring status, and closing it safely.

### Objectives
* Control Java process from Python code without system shells.
* Capture process exit status and handle server crashes.

### Deliverables
* `ProcessManager` service implementation.
* `/api/server/lifecycle` start/stop/restart endpoints.
* Background thread capturing subprocess exits.

### Tasks
1. Design `ServerProcessInterface` to permit future extensibility.
2. Implement python `subprocess.Popen` configuration within the `ProcessManager`.
3. Implement graceful stop script (sending `stop\n` to subprocess stdin pipe).
4. Build background watcher thread to check process exit code and trigger DB crash events.
5. Expose POST API endpoints to start, stop, and restart processes.

### Dependencies
* Phase 1 (Auth checks required for process actions).

### Risks
* Minecraft process hangs during stop command, blocking the event loop. (Mitigation: Implement a 30-second timeout, after which a SIGKILL signal is sent to force shutdown).

### Definition of Done
* Triggering "Start Server" spawns the `java` process in the background.
* Stopping the server sends the console command, saves world files, and terminates the subprocess cleanly.
* Process crashes register as `CRASHED` in the panel state indicator.

---

## Phase 3: Dashboard & Resource Telemetry
Exposing real-time system metrics to the frontend using WebSockets.

### Objectives
* Periodically gather system metrics (CPU, memory, disk).
* Deliver data updates continuously to UI widgets.

### Deliverables
* WebSocket route `/api/server/telemetry` for live metrics and player list distribution.
* Dashboard UI showing hardware graphs and server status controls.
* Metrics database archiving background worker.
* Web Audio API synthesized chimes controller for lifecycle and player events.

### Tasks
1. Set up a background metrics loop utilizing the `psutil` library.
2. Build connection manager to track active WebSocket telemetry subscribers.
3. Integrate canvas-based or SVG-based charting inside the React UI.
4. Store resource telemetry logs in the SQLite database every 60 seconds.
5. Create UI status banner representing the server state machine status.
6. Implement client-side Web Audio API synthesizers for started/stopped/restarted/joined/left events.
7. Build comparison hook tracking online players list and showing join/leave toast alerts.

### Dependencies
* Phase 2 completed.

### Risks
* SQLite database file becomes locked due to frequent resource logging. (Mitigation: Execute metrics commits on a secondary background thread using connection pooling, ensuring WAL mode is active).

### Definition of Done
* System CPU and memory changes update on the dashboard every 2 seconds.
* Active player count and list update in real time when players connect/disconnect, playing join/disconnect chimes and showing toast notifications.
* Database logs resource metrics, and successfully prunes entries older than 30 days.

---

## Phase 4: Console Log Streaming & Command Execution
Building the interactive command console window.

### Objectives
* Continuously stream subprocess stdout/stderr to connected browsers.
* Accept client terminal inputs and write to the subprocess input stream securely.

### Deliverables
* Streaming WebSocket connection for console logs.
* Interactive terminal input UI.
* Audit log tracking for executed console actions.

### Tasks
1. Build stdout/stderr reader thread to parse Minecraft log outputs.
2. Implement circular log buffer (last 2,000 lines) in backend memory.
3. Expose WebSocket console connection that pushes log frames in real time.
4. Build terminal component with search, filter, and color formatting.
5. Create POST route for executing console inputs, validating characters.
6. Commit every executed command to the `audit_logs` database table.

### Dependencies
* Phase 2 and Phase 3 completed.

### Risks
* Extremely verbose logs (e.g., debug modes or crash dumps) locking up the browser tab. (Mitigation: Use virtualized list loading on the React terminal to only render visible lines).

### Definition of Done
* Standard terminal logs render on-screen instantly as they appear in the process shell.
* Running commands like `/say Hello` prints the message in the game and logs the event under the active user's audit log.

---

## Phase 5: Backup Management
Building the world file archiving and recovery engine.

### Objectives
* Package world directories safely.
* Overwrite game directories during restoration without leaving orphan files.

### Deliverables
* Backup creation and restoration algorithms in `BackupService`.
* Database records mapping files, paths, and size checks.
* Backups management screen.

### Tasks
1. Write files compression algorithm utilizing python `zipfile` or `tarfile`.
2. Implement thread safe directory swap logic for database restoration.
3. Add in-game command triggers (`save-off`, `save-all`, `save-on`) to prevent database write conflicts during backups.
4. Build frontend Backup page with creation triggers and table lists.

### Dependencies
* Phase 2 completed.

### Risks
* World data is corrupted during a backup write. (Mitigation: Verify save write lock is completely disabled and flushed before initiating zip compress).

### Definition of Done
* Clicking "Create Backup" creates a compressed archive matching the database entry.
* Clicking "Restore" shuts down the game, extracts world files, and successfully restarts the server.

---

## Phase 6: Configuration Management
Writing and modifying Minecraft system configuration files.

### Objectives
* Edit `server.properties` and plugin settings securely.
* Validate data types before files are updated.

### Deliverables
* Config manager routes (`GET /api/config` / `POST /api/config`).
* Settings form fields with client and server-side validation checks.

### Tasks
1. Write a parser to convert `.properties` key-value files to JSON schemas.
2. Create directories sandbox resolver to validate path locations.
3. Implement a temporary files backup manager (e.g., save to `file.properties.tmp` first, then rename, to avoid partial write failures).
4. Develop configuration interface mapping validation structures.

### Dependencies
* Phase 1 and Phase 2 completed.

### Risks
* Directory path traversal vulnerability (`../../etc/passwd`). (Mitigation: Enforce strict path resolution checks comparing target path with root game directory).

### Definition of Done
* Properties display accurately in form fields with typed restrictions (e.g., integer inputs reject alphabetical text).
* Saved settings update the files on disk, and errors prevent files from being corrupted.

---

## Phase 7: Historical Monitoring & Auditing
Exposing system event logs and audit listings.

### Objectives
* View security-relevant actions and resource utilization charts.

### Deliverables
* Audit log viewer table in UI.
* Filter controls for logs.

### Tasks
1. Expose GET `/api/audit` endpoint supporting page parameters and sorting.
2. Build audit log viewer component with filter by user, action, and timestamp.
3. Implement daily log exporter (CSV/JSON output downloads).

### Dependencies
* Phase 4 completed.

### Risks
* Massive audit tables slowing query speeds. (Mitigation: Implement pagination and index database on `timestamp` and `user_id` columns).

### Definition of Done
* Admin can successfully search audit logs to view past events.
* System events (process crashes, restarts) display alongside the administrator actions.

---

## Phase 8: Security Hardening
Validating application limits, rate-limit settings, and sanitizing outputs.

### Objectives
* Protect the host OS from exploits.
* Mitigate denial-of-service attempts.

### Deliverables
* Rate limiting middleware configuration.
* Content Security Policy (CSP) headers.
* Input validation rules.

### Tasks
1. Implement `slowapi` or custom middleware to rate limit endpoints.
2. Enforce character whitelist sanitization on command strings.
3. Enforce secure CORS policy parameters.
4. Implement secure header configurations (HSTS, X-Content-Type-Options).

### Dependencies
* All preceding phases completed.

### Risks
* Arbitrary command injections via input fields. (Mitigation: Never pass user text directly to the system shell).

### Definition of Done
* Attempting brute-force logins triggers temporary rate-limit blocks (HTTP 429).
* Security scanners verify zero vulnerabilities for directory traversals or command injections.

---

## Phase 9: Production Deployment
Packaging the modular monolith for host system deployments.

### Objectives
* Deploy the application securely.
* Configure system process services for high availability.

### Deliverables
* Systemd service unit files.
* Production configuration guide.
* Automated startup configuration.

### Tasks
1. Write Systemd service definitions to launch FastAPI automatically on system startup.
2. Configure Nginx or Caddy as a reverse proxy with SSL certifications.
3. Build user configuration scripts to provision sandboxed system users (e.g. `minecraft-panel` user).

### Dependencies
* Phase 8 completed.

### Risks
* Permission failures when launching subprocesses using non-root service accounts. (Mitigation: Grant the panel service owner account read/write access to the Minecraft directories).

### Definition of Done
* System service boots panel on machine startup.
* Reverse proxy delivers panel UI over HTTPS.
