# 🛠️ Deep Survival Minecraft Server Panel

A premium, fully responsive, and feature-rich web management panel designed for administering Minecraft servers. Built with a unified dark-mode aesthetic, tactile animations, integrated audio notifications (chimes), and a responsive layout optimized for mobile phone browsers.

---

## 🌟 Key Features

### 1. Unified Telemetry Dashboard
* **Real-time Gauges**: Monitor system metrics (CPU usage, RAM allocation, concurrent player counts, disk space) dynamically via WebSocket connections.
* **SVG Timeline Charts**: Visually track hardware load histories (CPU and Memory) over time with smooth area gradients.
* **Server Address Copy**: A one-click copy badge for the server's IP address.

### 2. Interactive Shell Console
* **Live Command Stream**: Standard output and error logs streamed in real-time.
* **Tab-Triggered Autocomplete**: Type `/` to display a Minecraft-themed autocomplete suggestion list (e.g., `/say`, `/op`, `/whitelist add`, `/whitelist remove`, `/whitelist list`, `/whitelist on`, `/whitelist off`, `/ban`, `/pardon`, `/kick`, `/tp`, `/gamerule`, `/stop`, `/restart`, `/save-all`, `/save-on`, `/save-off`, `/difficulty`, `/gamemode`). Navigate suggestions with `ArrowUp`/`ArrowDown` and submit via `Tab`/`Enter`.
* **Smart Filter & Search**: Locate specific log records instantly using client-side query matching.

### 3. Responsive Mobile Viewports & LAN Binding
* **Mobile Sidebar Drawer**: Automatically transforms the collapsible desktop sidebar into a sliding drawer modal for devices under `768px`.
* **Touch-Dismiss Backdrop**: Tap anywhere outside the drawer to slide it closed.
* **Table Fallbacks**: Table layouts (like Panel Users and Audit Trails) seamlessly adapt to stacked Profile Cards and collapsible details to prevent horizontal scrolling.
* **Zero-Config LAN Exposure**: Vite configuration is bound to `0.0.0.0` (`host: true`), allowing local network devices (like a smartphone on the same Wi-Fi) to connect instantly.

### 4. Dynamic Reskinning & Custom Branding
* **Configurable Title**: The panel title can be dynamically changed globally via the backend configuration or environment variables.
* **Dynamic Custom Assets**: Zero-code reskinning by placing files in the public directory:
  * **Logo**: Detects `/logo.png` automatically and falls back to a signature emerald shield icon if missing.
  * **Moving Wallpaper**: Preloads `/background.png` or `/background.jpg`. When loaded, it applies a pseudo-random, 100-second looping 2D float translation (`translate3d`) behind a fixed vignette card shadow to mimic a cinematic moving camera.

### 5. Tactical Audio Chimes
* Synthesized sound notifications triggered on key lifecycle events:
  * **Server Starts**: Plays a melodic rising chime.
  * **Server Stops**: Plays a grounding descending chime.
  * **Server Restarts**: Plays a rhythmic alert chime.
  * **Player Joins**: Plays a lightweight alert.
  * **Player Disconnects**: Plays a soft warning note.

---

## 🛠️ Technology Stack

### Backend
* **FastAPI**: Core async REST API and WebSocket gateway.
* **SQLAlchemy & SQLite**: Audit trails, backup indices, and user authentication tables.
* **Pytest**: Standard Python test suite with async telemetry mocks.

### Frontend
* **Vite + React**: Fast frontend builds and state management.
* **TypeScript**: Strict compile-time typing.
* **Tailwind CSS**: Responsive utilities and layout variables.
* **Framer Motion**: Micro-animations and page transition overlays.
* **Lucide Icons**: Crisp vector UI icons.

---

## ⚙️ Environment Configuration

You can customize the panel's brand configurations through environment variables or backend settings:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PANEL_NAME` | The dynamic name displayed across the login, loading, and dashboard headers. | `"DEEP SURVIVAL"` |
| `DATABASE_URL` | SQLite database URI filepath location. | `"sqlite:///./minecraft_panel.db"` |

---

## 🚀 Getting Started

### 1. Backend Service Setup
1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Run the API database tests:
   ```powershell
   .venv\Scripts\python -m pytest
   ```
5. Start the FastAPI backend:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### 2. Frontend Development Setup
1. Navigate to the frontend directory:
   ```powershell
   cd ../frontend
   ```
2. Install npm packages:
   ```powershell
   npm install
   ```
3. Start the local Vite development server:
   ```powershell
   npm run dev
   ```
   *Note: Because LAN binding is enabled, Vite will print your local network address (e.g., `http://192.168.1.15:3000`). Scan or type this link into your phone browser to test mobile layouts.*

4. Compile the production assets:
   ```powershell
   npm run build
   ```

---

## 📂 Project Structure

```
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── config.py         # Configuration settings & env variables
│   │   ├── main.py           # API routing, status, and WS sockets
│   │   ├── models/           # SQLAlchemy schemas
│   │   └── services/         # Process monitoring & audit services
│   └── tests/                # Automated backend test suites
├── frontend/                 # Vite React Application
│   ├── public/               # Served static assets (background.png, logo.png)
│   ├── src/
│   │   ├── components/       # LoadingScreen, Logo, and shared indicators
│   │   ├── context/          # AuthContext & ToastContext layers
│   │   ├── hooks/            # WebSocket listeners
│   │   ├── pages/Dashboard/  # Core view wrappers
│   │   │   └── tabs/         # Modular tab subviews (Console, Access, Server)
│   │   ├── index.css         # Styling system & custom GPU keyframe animations
│   │   └── main.tsx          # React application entry-point
│   └── vite.config.ts        # Vite proxy and LAN binding configurations
└── deployment/               # Nginx & Systemd configuration files
```

---

## 📋 Deployment & Production Serving

A comprehensive deployment configuration is provided under `deployment/`:
* **Nginx Configuration**: `deployment/nginx.conf` sets up proxy headers for static web bundles, backend API endpoints, and WebSocket terminal flows.
* **Systemd Service**: `deployment/minecraft-panel.service` manages python background loops.
* Refer to [deployment_guide.md](file:///c:/Users/barnw/OneDrive/Documents/Projects/Minecraft/Minecraft%20Panel/deployment/deployment_guide.md) for step-by-step staging and production guides.
