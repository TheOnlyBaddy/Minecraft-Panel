# Project Tracking & Risk Register (Tracker)

## 1. Project Milestones

| ID | Milestone Name | Target Date | Status | Dependencies | Notes |
|---|---|---|---|---|---|
| **M0** | Project Setup & Base Architecture | Week 1 | Completed | None | Establish repo structures & initial DB setup |
| **M1** | Secure Authentication & RBAC Engine | Week 2 | Completed | M0 | Working user authentication and login pages |
| **M2** | Process Lifecycle Control Wrapper | Week 3 | Completed | M1 | Java subprocess management and state machine |
| **M3** | WebSockets Telemetry & Dashboard | Week 4 | Completed | M2 | Real-time graphs and server status updates |
| **M4** | Interactive Terminal Console | Week 5 | Completed | M3 | Live logs and interactive command input |
| **M5** | Backups & World Storage Engine | Week 6 | Completed | M2 | Compression, restore and rollback support |
| **M6** | Config sandboxing & Editor Form | Week 7 | Completed | M1, M2 | Server properties file editor and parser |
| **M7** | Audit Logging & Metrics Archiver | Week 8 | Completed | M4 | Searchable audit tables, daily metrics logs |
| **M8** | Production Hardening & Testing | Week 9 | Completed | M0 - M7 | Rate limit setups, pentesting, unit coverage |
| **M9** | High Availability System Deploy | Week 10 | Completed | M8 | Systemd unit scripts, reverse proxy configuration |

---

## 2. Active Task Tracker

| Task ID | Component | Title / Description | Priority | Assignee | Status | Target Date |
|---|---|---|---|---|---|---|
| **T-0.1** | Backend | Configure base FastAPI app structure & dependencies | High | Backend Eng | Completed | Week 1 |
| **T-0.2** | Database | Setup SQLAlchemy models and Alembic migrations | High | Backend Eng | Completed | Week 1 |
| **T-0.3** | Frontend | Initialize Vite React app with strict TypeScript | High | Frontend Eng| Completed | Week 1 |
| **T-1.1** | Security | Implement password hashing using passlib[bcrypt] | High | Sec Eng | Completed | Week 2 |
| **T-1.2** | Backend | Create JWT authentication routes and RBAC guards | High | Backend Eng | Completed | Week 2 |
| **T-2.1** | Process | Implement java process wrapper using `subprocess.Popen` | Critical | Backend Eng | Completed | Week 3 |
| **T-2.2** | Process | Build background process listener for crash alerts | High | Backend Eng | Completed | Week 3 |
| **T-3.1** | Backend | Set up metrics collector loop utilizing `psutil` | Medium | Backend Eng | Completed | Week 4 |
| **T-3.2** | Frontend | Build WebSocket telemetry client context | High | Frontend Eng| Completed | Week 4 |
| **T-4.1** | Process | Establish output reader threads for stdout/stderr logs| Critical | Backend Eng | Completed | Week 5 |
| **T-4.2** | Frontend | Build custom terminal UI utilizing virtualized scroll | High | Frontend Eng| Completed | Week 5 |
| **T-5.1** | Backup | Write world folders compression & extraction logic | Critical | Backend Eng | Completed | Week 6 |
| **T-6.1** | Config | Build settings parser and validator | Medium | Backend Eng | Completed | Week 7 |
| **T-7.1** | DB | Add system logs search and page filters | Low | Backend Eng | Completed | Week 8 |
| **T-8.1** | Security | Add endpoint rate limiting and CORS policies | High | Sec Eng | Completed | Week 9 |
| **T-9.1** | DevOps | Create systemd unit service files for autostart | Medium | DevOps Eng | Completed | Week 10 |
| **T-10.1** | Process | Implement flexible server launch (start.bat + Java fallback) | High | Backend Eng | Completed | Week 10 |
| **T-10.2** | Process | Implement playit.gg tunnel auto-detection & lifecycle sync | Medium | Backend Eng | Completed | Week 10 |
| **T-10.3** | Frontend | Implement mobile responsive sidebar drawer & card layouts | High | Frontend Eng| Completed | Week 10 |
| **T-10.4** | Frontend | Implement dynamic branding (panel name, logo, background) | Medium | Frontend Eng| Completed | Week 10 |
| **T-10.5** | Frontend | Implement tab-triggered autocomplete for console commands | Low | Frontend Eng| Completed | Week 10 |

---

## 3. Risk Register

| Risk ID | Description | Impact | Probability | Mitigation Strategy | Owner | Status |
|---|---|---|---|---|---|---|
| **R-1** | Out of Memory (OOM) killer terminates Minecraft process | High | High | Wrap process with memory limits and configure panel alert hooks to notify admins of memory exhaustion. | PM | Open |
| **R-2** | SQL injection or path traversal via configuration uploads | Critical | Low | Validate paths using `os.path.commonpath` and use parameterized queries in SQLAlchemy. | Sec Eng | Open |
| **R-3** | Browser locks up when rendering large console history logs | Medium | High | Use virtualized rendering components to display only visible lines of the console buffer. | Frontend | Open |
| **R-4** | SQLite database lock issues during concurrent log inserts | High | Medium | Enable WAL mode and configure database connection pooling with retry timeouts. | DevOps | Open |
| **R-5** | Backup generation times out or corrupts active world files | High | Low | Run `/save-off` and `/save-all` prior to compressing directory files, then resume writes with `/save-on`. | Backend | Open |

---

## 4. Active Blockers

| Blocker ID | Description | Impact | Owner | Mitigation Plan | Status |
|---|---|---|---|---|---|
| **B-1** | Java SDK environment missing on targeted test machines | Critical | DevOps Eng | Add environment validation check during setup script, halting launch if Java path is missing. | Proposed |

---

## 5. Architectural Decision Log

| Decision ID | Date | Decision Title | Status | Context & Rationale | Approved By |
|---|---|---|---|---|---|
| **ADR-001** | 2026-06-12 | Choose SQLite WAL for Initial DB | Approved | Simplicity of deployment, WAL mode mitigates locking issues, easy migration path to PG | Architect |
| **ADR-002** | 2026-06-12 | Bi-directional WebSockets | Approved | Minimizes log latency, supports raw interactive console command inputs directly | Architect |
| **ADR-003** | 2026-06-12 | Cookie-Based JWT Storage | Approved | Storing JWTs in HttpOnly cookies protects against XSS token extraction | Sec Eng |
| **ADR-004** | 2026-06-12 | Subprocess over Docker Wrapper | Approved | Provides compatibility with bare-metal setups and custom VPS instances | Lead Dev |
| **ADR-010** | 2026-06-14 | Flexible Server Launch Strategy | Approved | Cascading launch: prefer start.bat/start.sh, fall back to direct java -jar with configurable RAM | Lead Dev |
| **ADR-011** | 2026-06-14 | Playit.gg Tunnel Auto-Detection | Approved | Auto-detect and launch playit binary alongside server, sync lifecycle and stream logs | Lead Dev |
| **ADR-012** | 2026-06-14 | Mobile Responsive Sidebar Drawer | Approved | Transform sidebar into sliding drawer for mobile viewports under 768px | Lead Dev |

---

## 6. Change Log

| Version | Date | Author | Description of Changes | Approved By |
|---|---|---|---|---|
| **0.3.0** | 2026-06-14 | Lead Dev | Mobile responsive adaptation, playit.gg tunnel auto-detection, flexible server launch strategy (start.bat + direct Java fallback), dynamic panel branding, dynamic logo/background assets, tab-triggered console autocomplete, GPU-accelerated panning background, card-based mobile table layouts. | Lead Dev |
| **0.2.0** | 2026-06-14 | Lead Dev | Reskin dashboard with Deep Survival Theme, integrated Tailwind CSS, Web Audio API synthesizers, and player join/disconnect list telemetry. | Lead Dev |
| **0.1.0** | 2026-06-12 | Lead Architect | Initial Project Architecture definition, PRD, and Schema layouts | Architect |
