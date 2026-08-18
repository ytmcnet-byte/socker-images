#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=========================================="
echo "      SOCKER ENGINE AUTOMATIC INSTALLER   "
echo "=========================================="

BASE_RAW_URL="https://raw.githubusercontent.com/ytmcnet-byte/socker-images/main"
TARGET_DIR="$HOME/socker_engine"
BIN_DIR="$HOME/.local/bin"
ALT_BIN_DIR="$HOME/bin"

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
mkdir -p "$ALT_BIN_DIR"

# 3. Download core scripts directly from GitHub URLs
echo "[3/5] Downloading core scripts from GitHub..."
curl -sSL "$BASE_RAW_URL/socker.py" -o "$TARGET_DIR/socker.py"
curl -sSL "$BASE_RAW_URL/socker-image.py" -o "$TARGET_DIR/socker_image.py"
curl -sSL "$BASE_RAW_URL/socker-daemon.py" -o "$TARGET_DIR/socker_daemon.py"
curl -sSL "$BASE_RAW_URL/images.sh" -o "$TARGET_DIR/images.sh"

# 4. Set permissions & CLI shortcut
echo "[4/5] Setting execution permissions and PATH shortcuts..."
chmod +x "$TARGET_DIR/socker.py"
chmod +x "$TARGET_DIR/socker_image.py"
chmod +x "$TARGET_DIR/socker_daemon.py"
chmod +x "$TARGET_DIR/images.sh"

# Global Symlinks for immediate command recognition
ln -sf "$TARGET_DIR/socker.py" "$BIN_DIR/socker"
ln -sf "$TARGET_DIR/socker.py" "$ALT_BIN_DIR/socker"

# Export PATH in ~/.bashrc and current shell session
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "export PATH=\"\$HOME/.local/bin:\$HOME/bin:\$PATH\"" >> "$HOME/.bashrc"
fi
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"

# 5. Launch Socker Daemon in Background
echo "[5/5] Launching Socker Daemon..."

# Kill previous daemon instance if running
pkill -f "socker_daemon.py" 2>/dev/null || true
rm -f /tmp/socker.sock

# Start daemon using nohup
nohup python3 "$TARGET_DIR/socker_daemon.py" > "$TARGET_DIR/daemon.log" 2>&1 &

sleep 2

echo "=========================================="
echo " SUCCESS: Socker Engine Installed & Active! "
echo "=========================================="
echo "Socket Check:"
curl --unix-socket /tmp/socker.sock http://localhost/_ping 2>/dev/null || echo "Daemon initializing..."
echo ""
echo "Try running:"
echo "  socker ps"
echo "  socker run test_py --image python:3.11-slim python3 --version"
