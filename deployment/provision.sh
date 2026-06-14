#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Logging helpers
log_info() {
    echo -e "\e[32m[INFO]\e[0m $1"
}

log_error() {
    echo -e "\e[31m[ERROR]\e[0m $1" >&2
}

# 1. Enforce running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root (sudo)."
    exit 1
fi

log_info "Starting Antigravity Minecraft Panel production provisioning..."

# 2. Check system prerequisites
for cmd in python3 pip3 node npm nginx systemctl; do
    if ! command -v "$cmd" &> /dev/null; then
        log_error "Prerequisite '$cmd' is missing. Please install it first."
        exit 1
    fi
done

# 3. Create sandboxed minecraft user and group
if ! getent group minecraft &>/dev/null; then
    groupadd -r minecraft
    log_info "Created 'minecraft' system group."
fi

if ! getent passwd minecraft &>/dev/null; then
    useradd -r -g minecraft -d /var/www/minecraft-panel -s /sbin/nologin -c "Minecraft Panel Service User" minecraft
    log_info "Created 'minecraft' system user."
fi

# 4. Provision folder structure
TARGET_DIR="/var/www/minecraft-panel"
log_info "Setting up target directory at $TARGET_DIR..."
mkdir -p "$TARGET_DIR"

# Copy files from current working directory to target dir
# Excluding virtual envs, node_modules, and database files
log_info "Copying files to $TARGET_DIR..."
rsync -a --exclude='.git' --exclude='.venv' --exclude='node_modules' --exclude='dist' --exclude='backend/dev.db' --exclude='backend/test.db' ./ "$TARGET_DIR/"

# Create subdirectories if they don't exist
mkdir -p "/var/www/minecraft-server"
mkdir -p "$TARGET_DIR/backend/backups"

# 5. Set up Backend Python Virtual Environment
log_info "Setting up Python virtual environment..."
python3 -m venv "$TARGET_DIR/backend/.venv"
"$TARGET_DIR/backend/.venv/bin/pip" install --upgrade pip
log_info "Installing backend dependencies..."
"$TARGET_DIR/backend/.venv/bin/pip" install -r "$TARGET_DIR/backend/requirements.txt"

# 6. Set up Frontend Node Packages and Build
log_info "Installing frontend packages..."
(cd "$TARGET_DIR/frontend" && npm install)
log_info "Building production static assets..."
(cd "$TARGET_DIR/frontend" && npm run build)

# 7. Configure Permissions
log_info "Enforcing permissions for sandboxed execution..."
chown -R minecraft:minecraft "$TARGET_DIR"
chown -R minecraft:minecraft "/var/www/minecraft-server"
# Allow the minecraft user to execute scripts and run java
chmod -R 750 "$TARGET_DIR"
chmod -R 750 "/var/www/minecraft-server"

# 8. Deploy Systemd Unit Service
log_info "Registering Systemd Service..."
cp "$TARGET_DIR/deployment/minecraft-panel.service" /etc/systemd/system/minecraft-panel.service
systemctl daemon-reload
systemctl enable minecraft-panel.service
systemctl restart minecraft-panel.service
log_info "minecraft-panel service registered, enabled, and started."

# 9. Configure Nginx Reverse Proxy
log_info "Configuring Nginx reverse proxy..."
cp "$TARGET_DIR/deployment/nginx.conf" /etc/nginx/sites-available/minecraft-panel
ln -sf /etc/nginx/sites-available/minecraft-panel /etc/nginx/sites-enabled/
# Remove default site if it exists to avoid port conflict on port 80
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
    log_info "Removed default Nginx site link."
fi

# Test and reload Nginx
nginx -t
systemctl reload nginx
log_info "Nginx configured and reloaded."

log_info "Provisioning completed successfully!"
echo -e "\n\e[32mAntigravity Panel is now running in production!\e[0m"
echo "--------------------------------------------------------"
echo "Backend: check status using 'sudo systemctl status minecraft-panel'"
echo "Frontend: Served by Nginx. Edit server name in /etc/nginx/sites-available/minecraft-panel"
echo "--------------------------------------------------------"
