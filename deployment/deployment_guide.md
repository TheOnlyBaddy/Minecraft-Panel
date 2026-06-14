# Production Deployment Guide - Antigravity Minecraft Panel

This guide details the procedure to deploy the Antigravity Panel in a secure, high-availability production environment.

## 1. System Requirements & Prerequisites
* **Operating System**: Linux (Ubuntu 22.04 LTS or Debian 12 recommended).
* **Dependencies**:
  * Java Runtime Environment (JDK 17 or 21) to launch the Minecraft server.
  * Python 3.10+ (with `venv` and `pip`).
  * Node.js (v18+) and npm (v9+) to compile the React frontend.
  * Nginx (for serving static files and reverse-proxying requests).
  * Systemd (for service daemonization).
  * Rsync (for file transfer).

---

## 2. Quick Setup (Automated Install)
An automated script is provided in `deployment/provision.sh` to provision the environment.

1. Clone or copy the project directory to your server (e.g. at `/tmp/minecraft-setup`).
2. Navigate to the directory and run the provisioner as root:
   ```bash
   chmod +x deployment/provision.sh
   sudo ./deployment/provision.sh
   ```
3. The script will:
   * Create a sandboxed `minecraft` user.
   * Move files to `/var/www/minecraft-panel`.
   * Configure backend python virtual environment.
   * Build the React frontend static bundle.
   * Install and start the `minecraft-panel` systemd service.
   * Link the Nginx proxy site configuration.

---

## 3. Manual Step-by-Step Installation

If you prefer to configure the components manually, follow these steps:

### Step A: System User Sandboxing
For safety, we run all operations under a dedicated non-login system user:
```bash
sudo groupadd -r minecraft
sudo useradd -r -g minecraft -d /var/www/minecraft-panel -s /sbin/nologin -c "Minecraft Panel Service" minecraft
```

### Step B: Directories & Source Files
1. Copy the project panel folder to `/var/www/minecraft-panel`.
2. Create the separate Minecraft server folder:
   ```bash
   sudo mkdir -p /var/www/minecraft-server
   ```
3. Configure permissions for both directories:
   ```bash
   sudo chown -R minecraft:minecraft /var/www/minecraft-panel /var/www/minecraft-server
   sudo chmod -R 750 /var/www/minecraft-panel /var/www/minecraft-server
   ```

### Step C: Backend Setup
1. Create the virtual environment and install packages:
   ```bash
   cd /var/www/minecraft-panel/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. Place the Minecraft `paper.jar` (or other server jar) inside the `/var/www/minecraft-server/` folder. Ensure it is named `paper.jar` (or adjust the `MINECRAFT_JAR_NAME` setting in `app/config.py`).
3. Set environment variables. Create a `.env` file in `/var/www/minecraft-panel/backend/` containing:
   ```env
   SECRET_KEY=generate-a-secure-random-64-character-key
   MINECRAFT_SERVER_DIR=/var/www/minecraft-server
   ```

### Step D: Frontend Build Compilation
Build the React production bundle using Node.js:
```bash
cd /var/www/minecraft-panel/frontend
npm install
npm run build
```
The build outputs a static directory at `/var/www/minecraft-panel/frontend/dist`.

### Step E: Daemonize Backend with Systemd
1. Copy the systemd service file:
   ```bash
   sudo cp /var/www/minecraft-panel/deployment/minecraft-panel.service /etc/systemd/system/minecraft-panel.service
   ```
2. Edit `/etc/systemd/system/minecraft-panel.service` if you need to adjust JVM RAM allocations or target paths.
3. Reload, enable, and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable minecraft-panel.service
   sudo systemctl start minecraft-panel.service
   ```

### Step F: Configure Nginx & SSL
1. Copy the Nginx site configuration:
   ```bash
   sudo cp /var/www/minecraft-panel/deployment/nginx.conf /etc/nginx/sites-available/minecraft-panel
   sudo ln -sf /etc/nginx/sites-available/minecraft-panel /etc/nginx/sites-enabled/
   ```
2. Edit `/etc/nginx/sites-available/minecraft-panel` and change `server_name` to your domain (e.g. `panel.my-server.com`).
3. (Recommended) Configure SSL using Certbot (Let's Encrypt):
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d panel.my-server.com
   ```
4. Test configuration and restart:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## 4. Diagnostics & Troubleshooting

### Check Service Status
```bash
sudo systemctl status minecraft-panel
```

### Inspect Backend Daemon Logs
To view live logs from the FastAPI panel server:
```bash
sudo journalctl -u minecraft-panel.service -f
```

### Reset / Force Start Minecraft Server
If the Minecraft subprocess gets locked, restart the panel service. The systemd service will terminate the existing process tree safely and re-initialize the hooks.
```bash
sudo systemctl restart minecraft-panel
```
