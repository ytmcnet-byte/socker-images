#!/usr/bin/env python3
"""
SOCKER IMAGE ENGINE v1.1
Fetch manifest & archives from ytmcnet-byte/socker-images
"""

import os
import sys
import json
import urllib.request
import tarfile

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/ytmcnet-byte/socker-images/refs/heads/main"
CACHE_DIR = os.path.expanduser("~/socker_engine/cache")
MANIFEST_CACHE = os.path.join(CACHE_DIR, "manifest.json")

os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_manifest():
    manifest_url = f"{GITHUB_RAW_BASE}/dist/manifest.json"
    print(f"[socker-image] Fetching manifest from: {manifest_url}")
    try:
        req = urllib.request.Request(manifest_url, headers={'User-Agent': 'Socker-Engine/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            with open(MANIFEST_CACHE, "w") as f:
                json.dump(data, f, indent=2)
            return data
    except Exception as e:
        print(f"[socker-image] Error fetching manifest: {e}")
        if os.path.exists(MANIFEST_CACHE):
            print("[socker-image] Using cached manifest.json")
            with open(MANIFEST_CACHE, "r") as f:
                return json.load(f)
        return {}

def pull_and_unpack(image_tag, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    manifest = fetch_manifest()

    tarball_name = manifest.get(image_tag)
    if not tarball_name:
        print(f"[socker-image] Warning: Tag '{image_tag}' not found in manifest. Defaulting to alpine_rootfs.tar.gz")
        tarball_name = "alpine_rootfs.tar.gz"

    local_tarball = os.path.join(CACHE_DIR, tarball_name)
    download_url = f"{GITHUB_RAW_BASE}/dist/{tarball_name}"

    if not os.path.exists(local_tarball):
        print(f"[socker-image] Downloading {tarball_name} from GitHub...")
        try:
            req = urllib.request.Request(download_url, headers={'User-Agent': 'Socker-Engine/1.0'})
            with urllib.request.urlopen(req) as response, open(local_tarball, 'wb') as out_file:
                out_file.write(response.read())
            print(f"[socker-image] Download complete: {tarball_name}")
        except Exception as e:
            print(f"[socker-image] Failed to download {tarball_name}: {e}")
            return False
    else:
        print(f"[socker-image] Using cached archive: {tarball_name}")

    print(f"[socker-image] Extracting to {target_dir}...")
    try:
        with tarfile.open(local_tarball, "r:*") as tar:
            tar.extractall(path=target_dir)
        print(f"[socker-image] Image unpack successful!")
        return True
    except Exception as e:
        print(f"[socker-image] Extraction failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 2:
        tag = sys.argv[1]
        out_dir = sys.argv[2]
        pull_and_unpack(tag, out_dir)
    else:
        print("Usage: python3 socker_image.py <image_tag> <target_directory>")

