# Project Engineering Rules (Rules)

## 1. Architecture Rules

### Mandatory Practices
* **Separation of Concerns**: The application must be partitioned into strict layers: API, Service, Repository, and Model layers. Business decisions must not be executed inside route controllers.
* **Interface-Driven Process Control**: All process operations must interface through `ServerProcessInterface` to permit changing execution targets (e.g., switching to Docker containers) without breaking downstream code.
* **State Immutability**: Services must not persist state globally. All states must be loaded from data models or handled via explicit, locked process instances (like the process manager instance).
* **Process Lifecycle Coupling**: Auxiliary processes (like tunnel agents) must be lifecycle-bound to the primary server process. When the server stops, all coupled subprocesses must be terminated automatically.

### Recommended Practices
* Restrict domain-specific service logic from calling other service domains directly where possible; use events or shared repositories instead.
* Utilize Python standard typing definitions (Type Hints) on every method and function signature.

### Prohibited Practices
* **No Inline Queries**: Never invoke database queries directly inside service layers or route controllers. All database interactions must use repository abstractions.
* **No Direct File Access**: Do not perform file read/write operations within endpoints. Use the `ConfigService` or `BackupService` exclusively.

---

## 2. Backend Rules

### Mandatory Practices
* **Async Event Handling**: Use async endpoints (`async def`) for routes that perform IO operations (like database lookups or HTTP calls) to prevent thread blockages.
* **Strict Pydantic Validation**: All POST, PUT, and PATCH request bodies must map to Pydantic models for automatic validation and type enforcement.
* **Dependency Injection**: Utilize FastAPI's `Depends` for injection of database sessions, settings, and authenticators.

### Recommended Practices
* Use Python's standard library `pathlib.Path` for path manipulations instead of string concatenations.
* Keep function lengths under 50 lines. Extract complex logic into smaller sub-methods.

### Prohibited Practices
* **No Global Variables**: Never store stateful objects (like database connections, active process references, or session mappings) in global module-level variables. Use state containers managed by dependencies.
* **No Standard Prints**: Do not use `print()` statements for diagnostic checks. Use the structured logger exclusively.

---

## 3. Frontend Rules

### Mandatory Practices
* **Strict TypeScript**: Set `strict: true` in `tsconfig.json`. Do not use the `any` type under any circumstances.
* **Utility-First Styling**: Use Tailwind CSS for component styling. Do not write custom CSS stylesheets or classes outside standard utility attributes; define core theme structures in `index.css` or Tailwind configuration directives.
* **State Cleanup**: Always return cleanup functions in React `useEffect` hooks (e.g., disconnecting WebSockets, clearing timers, or removing event listeners).
* **Mobile-First Responsive Design**: All UI layouts must be tested on viewports as narrow as 375px. Use Tailwind responsive breakpoints (`md:`, `lg:`) for progressive enhancement rather than desktop-first degradation.
* **Dynamic Asset Detection**: Custom branding assets (logo, background) must be detected at runtime via HEAD preload requests, with graceful fallbacks when assets are missing.

### Recommended Practices
* Place component definitions in structured folders (e.g., `components/Button/Button.tsx`).
* Use custom React hooks (`useWebSocket`, `useMetrics`) to isolate business logic from presentation components.

### Prohibited Practices
* **No Inline CSS**: Do not use style attributes (`style={{color: 'red'}}`) in JSX templates except for dynamically calculated dimensions (like progress bars).
* **No Direct DOM Mutation**: Never use `document.getElementById` or native DOM queries. Manage element states using React refs (`useRef`) and standard React state mechanisms.

---

## 4. API Rules

### Mandatory Practices
* **JSON Payload Format**: All API request and response bodies must use standard JSON formatting, except for file downloads (like backups) and stream connections.
* **Restful Endpoints**: Match resource patterns correctly (e.g., `GET /api/backups`, `POST /api/backups/create`, `DELETE /api/backups/{id}`).
* **Standard Status Codes**:
  * `200 OK` for successful read/update operations.
  * `201 Created` for successful resource creations.
  * `400 Bad Request` for user input validation errors.
  * `401 Unauthorized` for expired or invalid authentication.
  * `403 Forbidden` for permission failures (RBAC check failures).
  * `422 Unprocessable Entity` for request structure failures.
  * `500 Internal Server Error` for system crashes.

### Recommended Practices
* Version all APIs under prefix patterns (e.g., `/api/v1/...`).
* Embed error codes (e.g., `ERR_INSUFFICIENT_DISK`) in JSON error payloads to assist client-side diagnostic displays.

### Prohibited Practices
* **No Unauthenticated State Mutations**: Do not expose endpoints that modify state without requiring authentication and CSRF protection.

---

## 5. Database Rules

### Mandatory Practices
* **Foreign Key Enforcement**: Explicitly enable SQLite foreign keys on connection startup.
* **Schema Migrations**: All database schema changes must be declared using Alembic migration files. No direct raw modifications are allowed in production.
* **Parameterized Variables**: Use parameter binding (SQLAlchemy ORM constructs or `?` placeholders) on all database queries.

### Recommended Practices
* Structure indexes to cover columns used in `WHERE`, `ORDER BY`, and `JOIN` clauses.
* Write schema definitions designed for easy translation to PostgreSQL (e.g., avoid SQLite-specific column type assumptions).

### Prohibited Practices
* **No String Interpolation in SQL**: Never construct SQL query strings using string formatting (`f"SELECT * FROM users WHERE name = '{user}'"`). This prevents SQL injection attacks.
* **No Long-Running Locks**: Avoid locking transactions while waiting for slow network operations. Keep database transactions brief and execute them after network operations complete.

---

## 6. Security Rules

### Mandatory Practices
* **Disable Shell Subprocesses**: Specify `shell=False` inside all `subprocess.Popen` or `subprocess.run` executions.
* **Path Sanitization**: Validate all file access requests using `os.path.commonpath` to verify the targets lie within the designated sandbox folder.
* **JWT Storage Location**: Deliver JWTs inside HttpOnly, Secure, and SameSite=Strict cookies. Do not store tokens in `localStorage`.
* **Output Sanitization**: Escape all terminal output lines before rendering them to prevent cross-site scripting (XSS) or browser terminal escape injection exploits.

### Recommended Practices
* Implement CORS policies that permit only the explicitly declared frontend URL to connect.
* Configure rate limits on authentication endpoints (e.g., max 5 login requests per minute per IP address).

### Prohibited Practices
* **No Shell Command Interpolation**: Never accept user strings, append them to command variables, and execute them on the system.
* **No Hardcoded Secrets**: Do not write passwords, secret keys, or authentication tokens into source code files. Load secrets from environment variables.

---

## 7. Testing Rules

### Mandatory Practices
* **80% Code Coverage**: The backend service and domain model classes must maintain at least 80% coverage.
* **Mock Subprocesses**: Mock subprocess outputs and stream loops during unit testing to avoid running actual Java instances.
* **Test Isolation**: Run each database test in a transaction block that rolls back when completed, ensuring a clean slate for each test execution.

### Recommended Practices
* Write frontend unit tests utilizing React Testing Library for reusable components (like status indicators or custom buttons).
* Write integration tests simulating complete client flows (e.g., login, update configuration, verify changes).

### Prohibited Practices
* **No Network Operations in Tests**: Unit tests must not perform external network calls. Use mock tools to simulate responses.
* **No Production Database Overwrites**: Never run tests against active production database files. Use memory-backed databases (`sqlite:///:memory:`) for tests.

---

## 8. Git Rules

### Mandatory Practices
* **Feature Branches**: Never commit code changes directly to the `main` or `master` branch. All modifications must reside on feature branches (e.g., `feature/auth-implementation`, `bugfix/console-render`).
* **Linear History**: Rebase feature branches on main before merging to avoid merge bubbles.
* **Descriptive Commit Messages**: Use semantic prefix structures for commits (e.g., `feat: add console websocket streaming`, `fix: sanitize directory paths`).

### Recommended Practices
* Create Pull Requests for code reviews, requiring approvals from at least one developer before merges.
* Configure Git pre-commit hooks to run linters (Black, Flake8, ESLint) prior to allowing commits.

### Prohibited Practices
* **No Secrets Committed**: Do not commit configuration files containing passwords or keys (like `.env`). Add these files to `.gitignore`.
* **No Large Binaries**: Do not check in large binary assets (like Minecraft JAR logs, world folders, or database snapshots).

---

## 9. Documentation Rules

### Mandatory Practices
* **Docstring Requirements**: Every public class, service method, and helper function in the backend must include a descriptive docstring defining arguments, returns, and raised exceptions.
* **API Documentation**: Maintain OpenAPI (Swagger) annotations for all FastAPI endpoints.
* **Consistent Formats**: Write all files, documentation updates, and logs in standard Markdown formats.

### Recommended Practices
* Write setup guides and developer documentation alongside changes.
* Embed code comments only when explaining complex algorithms or non-obvious logic.

### Prohibited Practices
* **No Outdated Readmes**: Do not commit changes that modify operational behavior without updating the corresponding README or architecture documentation files.

---

## 10. Logging Rules

### Mandatory Practices
* **JSON Logging**: Configure production logging to output structured JSON structures to stdout/stderr.
* **Sanitize Log Payloads**: Ensure user passwords, session tokens, and credit card numbers are stripped or masked from logs.
* **Level Configuration**: Use appropriate severity levels:
  * `DEBUG` for verbose diagnostic messages during development.
  * `INFO` for general system events (startup, shutdown, logins).
  * `WARNING` for non-fatal errors (failed logins, backup retry).
  * `ERROR` for unexpected failures (crashes, DB locks).
  * `CRITICAL` for fatal events requiring system intervention (disk full, security breach).

### Recommended Practices
* Set up log file rotation with a maximum size of 10MB per file and a limit of 7 archived logs.

### Prohibited Practices
* **No Plain String Error Logs**: Never output exceptions without logging the full stack trace (using `logging.exception()` in except blocks).

---

## 11. Monitoring Rules

### Mandatory Practices
* **Telemetry Throttling**: Maintain system resources checks on a throttled loop (max 1 sample per second).
* **Alert Triggers**: Implement alerts that trigger warnings when disk utilization exceeds 85% or CPU usage stays at 100% for more than 5 minutes.

### Recommended Practices
* Expose a `/health` metrics endpoint returning system status for external monitoring engines (like Prometheus).

### Prohibited Practices
* **No Infinite Loops**: Never run metrics monitoring loops without sleep intervals or cancel tokens.

---

## 12. Refactoring Rules

### Mandatory Practices
* **Regression Safety**: Do not modify legacy code structures without verifying that the existing test suite passes successfully.
* **Incremental Updates**: Break large refactoring tasks into separate commits or pull requests to simplify reviews.

### Recommended Practices
* Regularly run code smell scans (e.g., SonarQube, Radon) to monitor complexity metrics.

### Prohibited Practices
* **No Architectural Deviation**: Do not change component boundary interfaces without creating an Architecture Decision Record (ADR) and securing approval.
