# Product Requirements Document (PRD)

## 1. Executive Summary
The Minecraft Server Management Platform (codename: **Antigravity Panel**) is a production-grade, secure, web-based control panel designed for remote administration of Minecraft servers. The initial target server implementation is a Paper Minecraft Server, but the system architecture is designed to support future modular expansion to other server implementations (e.g., Vanilla, Fabric, Forge, BungeeCord, Velocity). It enables administrators to manage server lifecycles, monitor system metrics in real time, view console logs, execute commands securely, manage backups, and configure settings—all through a modern, responsive web application.

---

## 2. Vision
To provide Minecraft server administrators with a modern, elegant, and secure administrative interface that eliminates the need for SSH access, manual terminal commands, or direct SFTP configuration editing. The platform will serve as the single source of truth for server lifecycle, monitoring, backups, and configurations, ensuring high operational stability and professional-grade security.

---

## 3. Product Goals
* **Operational Autonomy**: Empower administrators and non-technical staff (e.g., moderators) to safely perform routine server management tasks without exposing host system credentials.
* **Security-First Administration**: Prevent security exploits by restricting web terminal inputs, enforcing Role-Based Access Control (RBAC), and sanitizing all inputs/outputs.
* **Proactive Monitoring**: Provide clear visibility into resource utilization (CPU, Memory, Disk) and server health to prevent downtime and out-of-memory crashes.
* **Data Protection**: Ensure automatic and manual backups can be generated, restored, and deleted easily to minimize data loss.
* **Auditability**: Track all actions performed on the platform to maintain accountability and assist in post-incident analysis.

---

## 4. Problem Statement
Managing a Minecraft server today is often fragmented and insecure:
1. **Security Vulnerabilities**: Sharing SSH/SFTP access with junior administrators or moderators poses severe security risks to the host system.
2. **Operational Overhead**: Tasks like modifying configurations, generating backups, and reading logs require command-line knowledge or raw file manipulation.
3. **Lack of Visibility**: Checking server status and resource utilization requires connecting to the host machine via SSH and running system utilities (e.g., `top`, `df`), which is not feasible for non-technical users.
4. **Crash Recovery**: If a server crashes due to memory leakage or a corrupted plugin, administrators without terminal access cannot restart it.

---

## 5. User Personas

### Persona A: The Owner (Alex)
* **Role**: Primary Server Administrator / System Owner.
* **Technical Level**: High. Comfortable with Linux, Docker, Python, and networking.
* **Goal**: Wants a stable, automated, and secure panel to manage the server and delegate tasks safely.
* **Frustrations**: Tired of writing custom bash scripts for backups and monitoring. Dislikes giving full SSH access to helpers.

### Persona B: The Moderator (Jordan)
* **Role**: In-Game Staff / Helper.
* **Technical Level**: Low-to-Medium.
* **Goal**: Needs to monitor player counts, restart the server if it hangs, check server uptime, and view the console log to troubleshoot player issues.
* **Frustrations**: Cannot access the terminal when the server crashes while Alex is offline. Has no way to check server performance.

### Persona C: The Developer (Taylor)
* **Role**: Plugin Configurator / Developer.
* **Technical Level**: Medium-to-High.
* **Goal**: Needs to modify configuration files (`server.properties`, plugin ymls), inspect error logs in the console, and take manual backups before updating plugins.
* **Frustrations**: Has to wait for Alex to upload files or edit configs manually via SFTP.

---

## 6. User Stories

### Authentication & Authorization
* **US-1.1**: As an administrator, I want to log in using secure credentials so that unauthorized users cannot access my server control panel.
* **US-1.2**: As an administrator, I want my sessions to expire after a period of inactivity so that unauthorized users cannot use an unattended browser session.
* **US-1.3**: As the system owner, I want to create user accounts with different permission levels (Admin vs. Moderator) so that I can restrict access to sensitive tasks (like config editing and backup restoration).

### Dashboard & Monitoring
* **US-2.1**: As an administrator, I want to view CPU, memory, and disk usage on a dashboard so that I can monitor server health at a glance.
* **US-2.2**: As an administrator, I want to see the active player count and current uptime so that I know if the server is active and running smoothly.
* **US-2.3**: As an administrator, I want to see the status of the last backup operation so that I can quickly verify that our data is protected.

### Server Lifecycle Management
* **US-3.1**: As an administrator, I want to start the Minecraft server via the web UI so that I don't have to access the command line.
* **US-3.2**: As an administrator, I want to stop the Minecraft server safely (running the `/stop` command internally) so that world data is saved correctly before shutdown.
* **US-3.3**: As an administrator, I want to force-restart the server if it hangs or stops responding so that player downtime is minimized.

### Console Management
* **US-4.1**: As an administrator, I want to see a live-streaming log of the Minecraft server console so that I can monitor in-game events and errors.
* **US-4.2**: As a developer, I want to search and filter console history so that I can troubleshoot past errors and trace plugin stack traces.
* **US-4.3**: As an administrator, I want to execute command-line inputs (e.g., `/op`, `/ban`) through a console command box so that I can manage the game server in real time.
* **US-4.4**: As the system owner, I want every console command executed via the web UI to be logged under the executing user's account in the audit log.

### Configuration Management
* **US-5.1**: As a developer, I want to view and edit `server.properties` and YAML configuration files directly in a web editor with validation so that I don't introduce syntax errors.
* **US-5.2**: As an administrator, I want to see a changelog of configuration edits so that I can roll back settings if the server fails to load.

### Backup Management
* **US-6.1**: As an administrator, I want to trigger a manual backup of the world files and configuration files before performing upgrades.
* **US-6.2**: As an administrator, I want to view a list of existing backups, including their creation date, file size, and status.
* **US-6.3**: As the system owner, I want to restore a previous backup to rollback corrupt states or delete outdated backups to free up disk space.

### Audit Logging
* **US-7.1**: As the system owner, I want to view an immutable log of all actions taken on the panel (e.g., logins, restarts, config edits, backup restorations) with timestamps and IP addresses for compliance and security audit purposes.

---

## 7. Functional Requirements

| ID | Module | Title | Description | Priority |
|---|---|---|---|---|
| **FR-1.1** | Auth | User Authentication | Username and password verification using password hashing (Argon2id/bcrypt). | P0 |
| **FR-1.2** | Auth | Session Management | Secure token-based session management (JWT or secure HTTP-only cookies). | P0 |
| **FR-1.3** | Auth | RBAC | Enforce role permissions: Admin (all operations) and Moderator (read-only, lifecycle control, write to console, no backup restore, no config write). | P0 |
| **FR-2.1** | Dash | Real-time Resource Stats | Stream system-level metrics (CPU, RAM, Disk, active player count, and active player usernames list) to the client every 2 seconds via WebSockets. | P0 |
| **FR-2.2** | Dash | Status Indicators | Visual indicator representing whether the Minecraft server is `STOPPED`, `STARTING`, `RUNNING`, or `CRASHED`. | P0 |
| **FR-2.3** | Dash | Server Lifecycle Audio Chimes | Play synthesized 8-bit sound effects (chimes) in the browser on server status changes (Start, Stop, Restart). | P1 |
| **FR-2.4** | Dash | Player Event Audio Chimes | Play synthesized 8-bit sound effects (chimes) and show name-specific toast alerts on player joins and disconnects. | P1 |
| **FR-3.1** | Lifecycle | Process Control | Launch the Paper jar file as a managed subprocess. Send signals for termination. | P0 |
| **FR-3.2** | Lifecycle | Graceful Shutdown | When stopping the server, send `stop` command to standard input rather than immediately killing the process. | P0 |
| **FR-4.1** | Console | Real-time Stream | Stream standard output (stdout) and error (stderr) of the Minecraft process via WebSockets. | P0 |
| **FR-4.2** | Console | Command Input | Text field allowing users to type and send Minecraft commands (without prefixing `/`) to standard input. | P0 |
| **FR-5.1** | Config | Properties Editor | Interface to parse, edit, validate, and write back `server.properties`. | P1 |
| **FR-5.2** | Config | Configuration Validation| Validate value types (e.g., `max-players` must be an integer > 0) before saving changes. | P1 |
| **FR-6.1** | Backup | Create Backup | Package game directories (excluding cache and logs) into a compressed tarball or zip file. | P0 |
| **FR-6.2** | Backup | Restore & Delete | Extract backup archive over the current game directory after stopping the process. Delete backup files. | P0 |
| **FR-7.1** | Audit | Event Logging | Log user ID, action name, IP address, user agent, timestamp, and metadata. Saved in database. | P0 |
| **FR-8.1** | Monitoring| Historical Metrics | Save system and game metrics (average tick rate if reachable, player count, RAM usage) to SQLite database at 1-minute intervals. Retain for 30 days. | P1 |

---

## 8. Non-Functional Requirements

### Security
* **NFR-SEC-1**: Password hashes must never be stored in plain text. Use bcrypt or Argon2id.
* **NFR-SEC-2**: All API endpoints must be protected by authentication middleware, except public auth endpoints.
* **NFR-SEC-3**: No system shell injection is permitted. Minecraft execution must use python `subprocess.Popen` with an array of strings (e.g., `["java", "-jar", ...]`) and `shell=False`.
* **NFR-SEC-4**: Command input must validate characters to prevent terminal escape sequence exploits.

### Performance & Responsiveness
* **NFR-PERF-1**: Dashboard loading time should be under 500ms for metadata.
* **NFR-PERF-2**: WebSocket telemetry updates must consume less than 10Kbps bandwidth per open client connection.
* **NFR-PERF-3**: Log scrolling must not lock the UI thread. Use virtualized lists (windowing) for console logs containing > 1,000 lines.

### Reliability & Resilience
* **NFR-REL-1**: If the Minecraft server process terminates unexpectedly (crashes), the panel must detect it, change status to `CRASHED`, and write the exit code to the event log.
* **NFR-REL-2**: Database operations must use connection pooling and transaction isolation to prevent SQLite locks.

### Extensibility & Maintainability
* **NFR-MAINT-1**: The backend code must achieve at least 80% unit test coverage for services and domain logic.
* **NFR-MAINT-2**: The frontend must be fully typed using TypeScript and linted using ESLint configurations.
* **NFR-EXT-1**: The process management layer must be defined by an interface (`ServerProcessInterface`), allowing the application to wrap other game servers (e.g., vanilla Java, Bedrock, dockerized servers) in the future.

---

## 9. Acceptance Criteria
1. **Security Verification**: Passing a security scan verifying that executing a command in the panel terminal does not execute operating system shell commands.
2. **Lifecycle Performance**: Starting and stopping the Minecraft process via the panel must accurately update the UI state within 1 second of process change.
3. **Data Integrity**: Restoring a backup must successfully revert the world directory to the exact state at the time of backup creation.
4. **Metrics Accuracy**: Displayed CPU and RAM utilization must match values reported by the operating system (within 5% margin).

---

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| **Minecraft Out-of-Memory (OOM) Crash** | High | High | Panel monitors memory usage and system resources. The wrapper automatically captures exit code `137` (OOM kill) and flags a specific OOM crash message to the admin. |
| **Disk Space Exhaustion via Backups** | High | Medium | Implement backup quotas (limit number of stored backups) and display warning banners on the dashboard when disk usage exceeds 85%. |
| **Direct Command Injection Exploit** | High | Low | Never construct command strings using shell interpolation. Always pass commands as arguments using structured lists in `subprocess.Popen(shell=False)`. |
| **WebSocket Connection Drops** | Medium| High | Frontend client implements exponential backoff reconnection strategies with visual "reconnecting" banners. |

---

## 11. Assumptions & Dependencies
* **Java Runtime**: The target host machine must have Java Development Kit (JDK) 17 or 21 pre-installed and added to the system `PATH` to launch the Paper Minecraft server.
* **OS Compatibility**: The platform backend is designed to run on Windows and Linux systems.
* **Single Server instance**: The initial version assumes a single Minecraft server directory managed by a single instance of the management panel.

---

## 12. Success Metrics
* **99.9% Uptime** of the management panel process itself.
* **Zero unauthorized logins** or session hijack events.
* **Backup success rate > 99.5%** with automated daily verification.
* **UI Load Latency < 300ms** on desktop and mobile web devices.

---

## 13. Future Roadmap
* **Phase A**: Multi-server orchestration (manage multiple instances from a single panel master).
* **Phase B**: Modpack and Plugin Installer (one-click integration with Modrinth and CurseForge APIs).
* **Phase C**: Schedule Manager (cron-like system for scheduling in-game commands, restarts, and backups).
* **Phase D**: SFTP Access (expose a sandboxed SFTP server integrated with panel accounts to transfer files).
