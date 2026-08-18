#!/bin/bash

# Configuration
SOCKER_DIR="$HOME/.socker_engine"
RAW_URL="https://raw.githubusercontent.com/ytmcnet-byte/socker-images/refs/heads/main/socker.py"

echo "--- Socker Non-Root Installation Start ---"

# 1. Create directory in user home
mkdir -p "$SOCKER_DIR"

# 2. Download socker.py
echo "Downloading socker.py..."
curl -L -o "$SOCKER_DIR/socker.py" "$RAW_URL"

# Check if download succeeded
if [ ! -f "$SOCKER_DIR/socker.py" ]; then
    echo "Error: Download failed!"
    exit 1
fi

# 3. Permissions
chmod +x "$SOCKER_DIR/socker.py"

# 4. Add to .bashrc for persistence
if ! grep -q "alias socker=" "$HOME/.bashrc"; then
    echo "Adding alias to ~/.bashrc..."
    echo "alias socker='$SOCKER_DIR/socker.py'" >> "$HOME/.bashrc"
    echo "export PATH=\$PATH:$SOCKER_DIR" >> "$HOME/.bashrc"
else
    echo "Alias already exists in ~/.bashrc"
fi

echo "--- Installation Complete! ---"
echo "Please run: source ~/.bashrc"
echo "You can now use 'socker' command directly."
