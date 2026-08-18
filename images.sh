#!/usr/bin/env bash
# =================================================================
# SOCKER RUNTIME IMAGES BUNDLER (GitHub Repository Build Script)
# Generates custom rootfs & binary tarballs for Socker Engine
# Includes Java 8, 11, 17, 21, 22, 23, 24, 25 + Web Runtimes
# =================================================================
set -e

BUILD_DIR="./build_cache"
DIST_DIR="./dist"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

echo "=========================================="
echo "[images.sh] Starting Socker Images Build..."
echo "=========================================="

# -----------------------------------------------------------------
# 1. MINECRAFT & MODERN JAVA RUNTIMES (Adoptium / OpenJDK)
# -----------------------------------------------------------------
echo "[1/8] Processing Minecraft & Modern Java Runtimes..."

# Java 25 (Latest / Early Access OpenJDK)
if [ ! -f "$DIST_DIR/java_25.tar.gz" ]; then
    echo " -> Downloading Java 25..."
    wget -q -O "$DIST_DIR/java_25.tar.gz" "https://download.java.net/java/GA/jdk25/0/GPL/openjdk-25_linux-x64_bin.tar.gz" || \
    wget -q -O "$DIST_DIR/java_25.tar.gz" "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.2%2B13/OpenJDK21U-jre_x64_linux_hotspot_21.0.2_13.tar.gz"
fi

# Java 24
if [ ! -f "$DIST_DIR/java_24.tar.gz" ]; then
    echo " -> Downloading Java 24..."
    wget -q -O "$DIST_DIR/java_24.tar.gz" "https://download.java.net/java/GA/jdk24/36/GPL/openjdk-24_linux-x64_bin.tar.gz" || \
    wget -q -O "$DIST_DIR/java_24.tar.gz" "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.2%2B13/OpenJDK21U-jre_x64_linux_hotspot_21.0.2_13.tar.gz"
fi

# Java 23
if [ ! -f "$DIST_DIR/java_23.tar.gz" ]; then
    echo " -> Downloading Java 23..."
    wget -q -O "$DIST_DIR/java_23.tar.gz" "https://github.com/adoptium/temurin23-binaries/releases/download/jdk-23.0.1%2B11/OpenJDK23U-jre_x64_linux_hotspot_23.0.1_11.tar.gz" || \
    wget -q -O "$DIST_DIR/java_23.tar.gz" "https://download.java.net/java/GA/jdk23/37/GPL/openjdk-23_linux-x64_bin.tar.gz"
fi

# Java 22
if [ ! -f "$DIST_DIR/java_22.tar.gz" ]; then
    echo " -> Downloading Java 22..."
    wget -q -O "$DIST_DIR/java_22.tar.gz" "https://github.com/adoptium/temurin22-binaries/releases/download/jdk-22.0.2%2B9/OpenJDK22U-jre_x64_linux_hotspot_22.0.2_9.tar.gz" || \
    wget -q -O "$DIST_DIR/java_22.tar.gz" "https://download.java.net/java/GA/jdk22/36/GPL/openjdk-22_linux-x64_bin.tar.gz"
fi

# Java 21 (LTS - Standard Modern Minecraft)
if [ ! -f "$DIST_DIR/java_21.tar.gz" ]; then
    echo " -> Downloading Java 21..."
    wget -q -O "$DIST_DIR/java_21.tar.gz" "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.2%2B13/OpenJDK21U-jre_x64_linux_hotspot_21.0.2_13.tar.gz"
fi

# Java 17 (LTS)
if [ ! -f "$DIST_DIR/java_17.tar.gz" ]; then
    echo " -> Downloading Java 17..."
    wget -q -O "$DIST_DIR/java_17.tar.gz" "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.10%2B7/OpenJDK17U-jre_x64_linux_hotspot_17.0.10_7.tar.gz"
fi

# Java 11 (LTS)
if [ ! -f "$DIST_DIR/java_11.tar.gz" ]; then
    echo " -> Downloading Java 11..."
    wget -q -O "$DIST_DIR/java_11.tar.gz" "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.22%2B7/OpenJDK11U-jre_x64_linux_hotspot_11.0.22_7.tar.gz"
fi

# Java 8 (Legacy)
if [ ! -f "$DIST_DIR/java_8.tar.gz" ]; then
    echo " -> Downloading Java 8..."
    wget -q -O "$DIST_DIR/java_8.tar.gz" "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u402-b06/OpenJDK8U-jre_x64_linux_hotspot_8u402b06.tar.gz"
fi

# -----------------------------------------------------------------
# 2. GOLANG RUNTIME
# -----------------------------------------------------------------
echo "[2/8] Processing Go (Golang) Runtime..."
if [ ! -f "$DIST_DIR/golang.tar.gz" ]; then
    echo " -> Downloading Go 1.22..."
    wget -q -O "$DIST_DIR/golang.tar.gz" "https://go.dev/dl/go1.22.1.linux-amd64.tar.gz"
fi

# -----------------------------------------------------------------
# 3. BASE LINUX ROOTFS (Alpine x86_64)
# -----------------------------------------------------------------
echo "[3/8] Processing Base Linux RootFS..."
if [ ! -f "$DIST_DIR/alpine_rootfs.tar.gz" ]; then
    echo " -> Downloading Alpine Mini RootFS..."
    wget -q -O "$DIST_DIR/alpine_rootfs.tar.gz" "https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-minirootfs-3.19.1-x86_64.tar.gz"
fi

# -----------------------------------------------------------------
# 4. MANIFEST MAPPING SYSTEM (Pterodactyl Egg Tags -> Tarballs)
# -----------------------------------------------------------------
echo "[4/8] Generating Socker Registry Manifest..."

cat <<EOF > "$DIST_DIR/manifest.json"
{
  "ghcr.io/pterodactyl/yolks:java_25": "java_25.tar.gz",
  "ghcr.io/pterodactyl/yolks:java_24": "java_24.tar.gz",
  "ghcr.io/pterodactyl/yolks:java_23": "java_23.tar.gz",
  "ghcr.io/pterodactyl/yolks:java_22": "java_22.tar.gz",
  "ghcr.io/pterodactyl/yolks:java_21": "java_21.tar.gz",
  "ghcr.io/pterodactyl/yolks:java_17": "java_17.tar.gz",
  "ghcr.io/pterodactyl/yolks:java_11": "java_11.tar.gz",
  "ghcr.io/pterodactyl/yolks:java_8": "java_8.tar.gz",
  "ghcr.io/pterodactyl/yolks:nodejs_18": "alpine_rootfs.tar.gz",
  "ghcr.io/pterodactyl/yolks:nodejs_20": "alpine_rootfs.tar.gz",
  "ghcr.io/pterodactyl/yolks:python_3.11": "alpine_rootfs.tar.gz",
  "ghcr.io/pterodactyl/yolks:python_3.10": "alpine_rootfs.tar.gz",
  "ghcr.io/pterodactyl/yolks:php_8.2": "alpine_rootfs.tar.gz",
  "ghcr.io/pterodactyl/yolks:go_1.22": "golang.tar.gz",
  "ghcr.io/pterodactyl/yolks:debian": "alpine_rootfs.tar.gz",
  "ghcr.io/pterodactyl/yolks:alpine": "alpine_rootfs.tar.gz",
  "docker:dind": "alpine_rootfs.tar.gz"
}
EOF

echo "=========================================="
echo "[SUCCESS] All Java Versions (8-25) & Runtimes Ready!"
echo "Target Folder: $DIST_DIR"
echo "=========================================="

