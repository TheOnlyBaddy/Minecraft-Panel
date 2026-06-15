# Architecture Decision Records (ADR)

This document records the architectural choices and technical decisions made for the design of the Minecraft Server Management Platform.

## Decision Template

Each record uses the following structured layout:

```markdown
### ADR-[Number]: [Title]

* **Status**: [Proposed / Accepted / Rejected / Superseded]
* **Date**: [YYYY-MM-DD]
* **Author**: [Name/Role]

#### Context
Describe the technical challenge, product requirements, or operational constraints that prompted this decision.

#### Decision
State the chosen solution clearly, describing the implementation scope.

#### Alternatives Considered
Detail other options that were evaluated and explain why they were not selected.

#### Consequences
Describe the outcomes of this decision, including positive benefits, negative tradeoffs, and downstream impacts.
```

---

## Decision Log

| ID | Title | Status | Date |
|---|---|---|---|
| **ADR-001** | Backend Framework Selection (FastAPI) | Accepted | 2026-06-12 |
| **ADR-002** | Real-time Communication Protocol (WebSockets) | Accepted | 2026-06-12 |
| **ADR-003** | Database Selection for Single Server (SQLite WAL) | Accepted | 2026-06-12 |
| **ADR-004** | Minecraft Process Wrapper Model (Subprocess Popen) | Accepted | 2026-06-12 |
| **ADR-005** | Session Storage Mechanism (HttpOnly JWT Cookies) | Accepted | 2026-06-12 |
| **ADR-006** | Frontend Styling System (CSS Modules) | Superseded by ADR-007 | 2026-06-12 |
| **ADR-007** | Adopt Tailwind CSS styling engine | Accepted | 2026-06-13 |
| **ADR-008** | In-Browser Synthesized Sound Effects (Web Audio API) | Accepted | 2026-06-13 |
| **ADR-009** | Telemetry Extension for Active Player Tracking | Accepted | 2026-06-14 |
| **ADR-010** | Flexible Server Launch Strategy (start.bat + Java Fallback) | Accepted | 2026-06-14 |
| **ADR-011** | Playit.gg Tunnel Agent Auto-Detection | Accepted | 2026-06-14 |
| **ADR-012** | Mobile Responsive Sidebar Drawer | Accepted | 2026-06-14 |

---

## Architecture Decisions

### ADR-001: Backend Framework Selection (FastAPI)

* **Status**: Accepted
* **Date**: 2026-06-12
* **Author**: Principal Software Architect

#### Context
The backend must support real-time operations, including WebSocket streaming for console logs and CPU metrics, alongside standard REST routes. The server must be lightweight, secure, and support easy integration with Python libraries (like `psutil` and `sqlite3`).

#### Decision
Use **FastAPI** as the core backend framework, running on Uvicorn (ASGI server) with python 3.10+.

#### Alternatives Considered
* **Django**: Too heavy and opinionated. Synchronous database patterns in Django make real-time WebSocket loops more complex.
* **Flask**: Simple, but lacks native async/WebSocket support. Running async tasks in Flask requires external task queues (like Celery) or WSGI-to-ASGI bridge layers.

#### Consequences
* **Positive**:
  * Out-of-the-box support for async routes and WebSockets.
  * Automatic OpenAPI (Swagger) generation simplifies API reviews.
  * Fast execution speeds, comparable to Node.js and Go frameworks.
  * Built-in dependency injection system.
* **Negative**:
  * Smaller ecosystem of pre-built administrative plugins compared to Django.
  * Requires explicit selection of third-party libraries for ORM (SQLAlchemy) and migration layers (Alembic).

---

### ADR-002: Real-time Communication Protocol (WebSockets)

* **Status**: Accepted
* **Date**: 2026-06-12
* **Author**: Senior Backend Engineer

#### Context
Administrators require real-time updates for server status indicators, CPU/RAM utilization charts, and interactive console logs. In addition, users need to write commands back to the server process stdin interactively.

#### Decision
Implement **WebSockets** as the single bi-directional transport protocol for live logs, metrics streams, and terminal inputs.

#### Alternatives Considered
* **Server-Sent Events (SSE) + HTTP POST**: SSE provides low-overhead one-way log streaming, while client commands could use standard REST HTTP POST requests. However, managing two separate transport protocols complicates frontend connection tracking and error recovery.
* **HTTP Polling**: Periodic polling (e.g., every 2 seconds) for logs and metrics is simple but introduces high latency, excessive network overhead, and database query stress.

#### Consequences
* **Positive**:
  * Low latency, full-duplex communication over a single TCP connection.
  * Interactive, responsive console experience for terminal inputs.
* **Negative**:
  * WebSockets require persistent connections, consuming server-side file descriptors and memory.
  * Stateful connections complicate load balancing if the application scales horizontally in the future (requires sticky sessions or a Redis backplane).
  * Proxy servers (like Nginx) require explicit configuration to support WebSocket connection upgrades.

---

### ADR-003: Database Selection for Single Server (SQLite WAL)

* **Status**: Accepted
* **Date**: 2026-06-12
* **Author**: Senior Backend Engineer / DevOps Engineer

#### Context
The panel is designed to run directly on the same physical host or virtual machine as the Minecraft server. Requiring a complex database installation increases deployment friction for users. However, the database must handle concurrent reads and writes, such as streaming metrics, audit logs, and authentication checks.

#### Decision
Deploy **SQLite** as the primary database, configured in **Write-Ahead Logging (WAL)** mode. Design database access patterns using SQLAlchemy ORM to maintain compatibility with PostgreSQL for future multi-server panel editions.

#### Alternatives Considered
* **PostgreSQL**: Offers superior concurrency, clustering, and data validation, but requires running a separate service container or host daemon, complicating the local installation process.
* **JSON/YAML files**: Reading and writing configuration files for audit logs and users avoids a database dependency but lacks transaction isolation, schema validation, and indexing, which are critical for audit logs and historical metrics.

#### Consequences
* **Positive**:
  * Single-file database with zero configuration or external process dependencies.
  * Fast read speeds and low resource utilization.
  * WAL mode allows readers to access data concurrently without blockages during write operations.
* **Negative**:
  * SQLite does not support remote network access.
  * Database size is constrained by local disk space.
  * SQLite does not enforce strict type checks natively. This must be managed at the application level (Pydantic / SQLAlchemy).

---

### ADR-004: Minecraft Process Wrapper Model (Subprocess Popen)

* **Status**: Accepted
* **Date**: 2026-06-12
* **Author**: Principal Software Architect

#### Context
The platform must execute, monitor, and stop the Minecraft Paper Java archive file. The execution must be secure, sandbox the panel against directory traversals, and capture exit codes reliably without introducing shell vulnerabilities.

#### Decision
Execute the Minecraft server process as a direct OS child subprocess using Python's `subprocess.Popen` with `shell=False` and structured argument lists.

#### Alternatives Considered
* **Docker Containers**: Running Minecraft inside a Docker container isolates the process and limits memory usage automatically. However, it requires Docker daemon installations on host systems, which is not supported in all hosting environments (e.g., restricted VPSs or custom Linux distributions).
* **Systemd wrapper**: Wrapping systemd services inside python endpoints is simple but limits platform compatibility to systemd-based Linux systems, preventing installation on Windows platforms.

#### Consequences
* **Positive**:
  * Works on Windows and Linux out of the box.
  * Direct control over stdin/stdout pipes allows real-time log parsing and command executions.
  * Eliminates shell execution vulnerabilities since `shell=False` bypasses the OS command interpreter.
* **Negative**:
  * The panel process requires privileges to launch the Java command, meaning a compromised panel could gain control of the user running the service.
  * Resource limits (CPU/RAM caps) must be managed programmatically or through the JVM command-line flags (e.g., `-Xmx8G`), rather than OS container limits.

---

### ADR-005: Session Storage Mechanism (HttpOnly JWT Cookies)

* **Status**: Accepted
* **Date**: 2026-06-12
* **Author**: Security Engineer

#### Context
JWT credentials must be transmitted to protected API routes. If these tokens are intercepted by malicious scripts or stored insecurely, unauthorized users could gain complete control over the Minecraft server.

#### Decision
Deliver signed JSON Web Tokens (JWT) inside **HttpOnly, Secure, and SameSite=Strict cookies**.

#### Alternatives Considered
* **LocalStorage Token Storage**: Storing the token in the browser's `localStorage` and passing it via the `Authorization: Bearer <token>` header is a common SPA pattern. However, `localStorage` is accessible to JavaScript, making it vulnerable to extraction via Cross-Site Scripting (XSS) attacks.

#### Consequences
* **Positive**:
  * **HttpOnly** cookie flag ensures JavaScript cannot read the token, mitigating XSS attacks.
  * **Secure** flag guarantees the cookie is only sent over encrypted HTTPS connections.
  * **SameSite=Strict** prevents the browser from sending the cookie with cross-site requests, mitigating Cross-Site Request Forgery (CSRF) attacks.
* **Negative**:
  * Requires CORS configuration to allow credential sharing between the frontend and backend domains if they run on different ports during development.
  * Cookie handling logic in FastAPI is slightly more complex than header extraction.

---

### ADR-006: Frontend Styling System (CSS Modules)

* **Status**: Superseded by ADR-007
* **Date**: 2026-06-12
* **Author**: Senior Frontend Engineer

#### Context
The frontend styling must support custom glassmorphic aesthetics, responsive layouts, and quick rendering performance without adding heavy build dependencies. The styling system must prevent class name collision issues as the component library grows.

#### Decision
Style UI elements using **Vanilla CSS with CSS Modules** (`*.module.css`) in the React-Vite project.

#### Alternatives Considered
* **Tailwind CSS**: Offers utility-first classes, but introduces versioning dependencies, requires setup steps, and can result in verbose JSX files that obscure structural layout logic.
* **Styled Components (CSS-in-JS)**: Provides scoping, but adds runtime performance overhead (parsing CSS in JS) and can lead to style hydration mismatch warnings during server-side builds.

#### Consequences
* **Positive**:
  * No external styling packages required, minimizing dependency bloat and installation issues.
  * CSS Modules dynamically scopes class names (e.g., `.button__xyz123`) to prevent name collisions.
  * Clean division between presentation JSX code and styling rules.
  * Full support for CSS custom variables, enabling dynamic theme adjustments (e.g., dark mode toggle).
* **Negative**:
  * Requires writing more CSS file declarations compared to Tailwind utility shortcuts.
  * Requires manual configuration of linting rules for CSS.

---

### ADR-007: Adopt Tailwind CSS styling engine

* **Status**: Accepted
* **Date**: 2026-06-13
* **Author**: Lead Frontend Engineer

#### Context
The product needs a reskin to implement the "Deep Survival" dark mode theme, requiring sophisticated layouts, glassmorphism cards, glowing emerald active navigation accents, and responsive collapsed states. Doing this in vanilla CSS modules resulted in duplicate stylesheets, verbose rules, and difficulty sharing style system tokens across components.

#### Decision
Adopt **Tailwind CSS** (v4.x) as the styling framework, replacing CSS modules. Standardize colors, transitions, and typography scale directly in `index.css` under the `@theme` directive.

#### Alternatives Considered
* **CSS Modules**: Rejected because maintaining complex hover animations, custom slots, and transitions across 9 tab views created substantial code duplication and styling debt.
* **Chakra UI / Material UI**: Rejected due to heavy runtime size, complex component setups, and difficulty fitting the custom pixel-art block aesthetic.

#### Consequences
* **Positive**:
  * Single file styling configuration, eliminating modular CSS overhead.
  * Extremely fast design iterations using utility classes.
  * Smaller bundle sizes since unused styles are automatically purged.
* **Negative**:
  * Clutters the JSX layouts with utility classes.
  * Requires a postcss compilation build pipeline dependency.

---

### ADR-008: In-Browser Synthesized Sound Effects (Web Audio API)

* **Status**: Accepted
* **Date**: 2026-06-13
* **Author**: Senior Frontend Engineer

#### Context
The user requested nostalgic 8-bit sound effects (chimes) played during server status transitions (start, stop, restart) and player events (join, leave). Requiring the backend to host or download MP3/WAV audio assets introduces bandwidth overhead, offline load failures, and asset resolution paths issues.

#### Decision
Synthesize all retro 8-bit audio effects directly in the client browser using the **Web Audio API** (`AudioContext`, `OscillatorNode`, and `GainNode` with exponential/linear decay envelopes).

#### Alternatives Considered
* **Static Audio Asset files**: Hosting static `.mp3` or `.wav` files and loading them via standard HTML5 `<audio>` elements. Rejected because it increases server storage, network load times, and can fail under local offline environments.

#### Consequences
* **Positive**:
  * Zero-bandwidth sound effects (generated programmatically in microseconds).
  * 100% offline-compatible (runs entirely client-side).
  * Highly customizable pitch, duration, envelopes, and waveform types (e.g. square, sawtooth, triangle waves).
* **Negative**:
  * Blocked by modern browser autoplay policies if no user interaction (clicks) has occurred on the page yet.

---

### ADR-009: Telemetry Extension for Active Player Tracking

* **Status**: Accepted
* **Date**: 2026-06-14
* **Author**: Senior Backend Engineer

#### Context
To trigger personalized player join and disconnect toast alerts and audio chimes, the frontend must detect which specific player connected or disconnected. The previous telemetry message only returned an integer count of active players (`active_players`), which is insufficient to determine player names.

#### Decision
Extend the metrics WebSocket telemetry payload to include `active_players_list` (a sorted list of usernames currently online) parsed from standard Minecraft server logs.

#### Alternatives Considered
* **HTTP Polling**: Polling `/api/server/players/online` every 2 seconds. Rejected because it generates unnecessary network calls and introduces lag.

#### Consequences
* **Positive**:
  * Zero extra network calls since telemetry WebSocket pushes the list automatically.
  * Permits showing real-time, name-specific toast notifications (e.g. `Alex joined the game`) alongside the audio chimes.
* **Negative**:
  * Marginally increases the size of the JSON payload streamed over WebSockets (negligible for typical server player limits).

---

### ADR-010: Flexible Server Launch Strategy (start.bat + Java Fallback)

* **Status**: Accepted
* **Date**: 2026-06-14
* **Author**: Lead Backend Engineer

#### Context
The server owner uses a custom `start.bat` batch script with specific JVM flags (e.g., `-Xms6G -Xmx6G`). However, the panel must also be able to start the server independently if `start.bat` is missing or if the user prefers direct Java execution via configurable environment variables.

#### Decision
Implement a **cascading launch strategy**: On Windows, first check for `start.bat` and execute it via `cmd.exe /c start.bat`. If not found, fall back to direct `java -jar paper.jar nogui` using RAM settings from `MINECRAFT_MIN_RAM` and `MINECRAFT_MAX_RAM` environment variables. On Linux, check for `start.sh` before falling back similarly.

#### Alternatives Considered
* **Always use start.bat**: Rejected because it prevents the panel from operating independently of the batch script.
* **Always use direct Java**: Rejected because it would ignore custom JVM flags in the user's existing batch script.

#### Consequences
* **Positive**:
  * Respects existing server configurations while providing full fallback autonomy.
  * RAM allocations are configurable through environment variables for the fallback path.
* **Negative**:
  * When using `start.bat`, the panel cannot dynamically override RAM settings—it uses whatever the batch script defines.

---

### ADR-011: Playit.gg Tunnel Agent Auto-Detection

* **Status**: Accepted
* **Date**: 2026-06-14
* **Author**: Lead Backend Engineer

#### Context
The server owner uses playit.gg to create public tunnels for the Minecraft server. The playit agent binary (`playit.exe` on Windows, `playit` on Linux) resides alongside the server files. The panel should automatically detect and launch this agent when starting the server.

#### Decision
After launching the Minecraft server subprocess, check for the playit.gg binary in the server directory. If found, spawn it as a separate async subprocess. Stream its stdout/stderr into the panel console with a `[playit.gg]:` prefix. Terminate the tunnel agent automatically when the server stops or the panel shuts down.

#### Alternatives Considered
* **Manual toggle in the panel UI**: Rejected to minimize configuration complexity for the initial implementation.
* **Systemd/Windows Service for playit**: Rejected because it decouples the tunnel lifecycle from the server lifecycle.

#### Consequences
* **Positive**:
  * Zero-configuration tunnel management—just place the playit binary in the server directory.
  * Tunnel lifecycle is perfectly synchronized with server lifecycle.
  * Tunnel logs are visible in the panel console for debugging.
* **Negative**:
  * The panel assumes that the playit binary in the server directory is properly configured. Misconfigured agents may produce errors.

---

### ADR-012: Mobile Responsive Sidebar Drawer

* **Status**: Accepted
* **Date**: 2026-06-14
* **Author**: Senior Frontend Engineer

#### Context
The panel must be accessible from mobile phone browsers on the same LAN network. The desktop sidebar navigation (with collapse/expand toggle) does not work well on small viewports, as it consumes too much horizontal space and prevents the main content from rendering properly.

#### Decision
On viewports under `768px`, transform the sidebar into a **sliding drawer overlay** controlled by a hamburger menu (☰) button. Add a semi-transparent backdrop that dismisses the drawer on tap. Convert table-based layouts (Access panel, audit trails) into vertically stacked profile cards to prevent horizontal scrolling.

#### Alternatives Considered
* **Bottom Tab Bar**: Common in mobile apps, but does not map well to the panel's 9+ navigation items.
* **Dropdown Menu**: Rejected because it lacks the spatial awareness of a sliding drawer.

#### Consequences
* **Positive**:
  * Full panel functionality is available on mobile phone browsers.
  * Touch-friendly interactions (tap to dismiss, swipe-ready drawer).
  * Table data remains readable without horizontal scrolling.
* **Negative**:
  * Drawer overlay requires careful z-index management to avoid conflicts with modals and toasts.
