#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=========================================="
echo "      SOCKER ENGINE AUTOMATIC INSTALLER   "
echo "=========================================="

BASE_RAW_URL="https://raw.githubusercontent.com/ytmcnet-byte/socker-images/refs/heads/main"
TARGET_DIR="$HOME/socker_engine"
BIN_DIR="$HOME/.local/bin"

# 1. Check Python3 and required dependencies
echo "[1/5] Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed. Please install Python3 first."
    exit 1
fi

python3 -c "import psutil" 2>/dev/null || {
    echo "Installing psutil library..."
    pip3 install psutil --quiet || python3 -m pip install psutil --quiet
}

# 2. Create directory structure
echo "[2/5] Setting up Socker Engine directories..."
mkdir -p "$TARGET_DIR/cache"
mkdir -p "$TARGET_DIR/containers"
mkdir -p "$BIN_DIR"

# 3. Download scripts from GitHub
echo "[3/5] Downloading core scripts from GitHub..."
curl -sSL "$BASE_RAW_URL/socker.py" -o "$TARGET_DIR/socker.py"
curl -sSL "$BASE_RAW_URL/socker-image.py" -o "$TARGET_DIR/socker_image.py"
curl -sSL "$BASE_RAW_URL/socker-daemon.py" -o "$TARGET_DIR/socker_daemon.py"
curl -sSL "$BASE_RAW_URL/images.sh" -o "$TARGET_DIR/images.sh"

# 4. Set permissions & CLI shortcut
echo "[4/5] Setting execution permissions..."
chmod +x "$TARGET_DIR/socker.py"
chmod +x "$TARGET_DIR/socker_image.py"
chmod +x "$TARGET_DIR/socker_daemon.py"
chmod +x "$TARGET_DIR/images.sh"

# Link socker.py to PATH for global CLI usage
ln -sf "$TARGET_DIR/socker.py" "$BIN_DIR/socker"

# Add ~/.local/bin to PATH if not present
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
    export PATH="$HOME/.local/bin:$PATH"
fi

# 5. Create and enable Systemd Service for daemon
echo "[5/5] Configuring background Socker Daemon service..."
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

cat << EOF > "$SERVICE_DIR/socker.service"
[Unit]
Description=Socker Non-Root Engine Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/socker_engine/socker_daemon.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now socker.service || echo "Warning: Systemd user service could not be started automatically."

echo "=========================================="
echo " SUCCESS: Socker Engine Installed!       "
echo "=========================================="
echo "Usage test:"
echo "  socker ps"
echo "  socker run test_id --image ghcr.io/pterodactyl/yolks:java_21 java -version"

