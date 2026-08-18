#!/usr/bin/env python3
"""
SOCKER DOCKER-HUB DIRECT PULL ENGINE v2.0
Directly fetches and extracts Docker Hub / OCI images without Docker Daemon.
"""

import os
import sys
import json
import tarfile
import urllib.request
import urllib.parse

CACHE_DIR = os.path.expanduser("~/socker_engine/cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def parse_image_tag(image_tag):
    """Image tag parsing (e.g., 'ubuntu:latest', 'pterodactyl/yolks:java_21', 'python:3.11-slim')"""
    if ":" in image_tag:
        name, tag = image_tag.split(":", 1)
    else:
        name, tag = image_tag, "latest"

    # Official Docker Hub images handling (e.g. 'ubuntu' -> 'library/ubuntu')
    if "/" not in name:
        name = f"library/{name}"

    # Handle domain prefixes like ghcr.io or docker.io
    if name.startswith("docker.io/"):
        name = name.replace("docker.io/", "")

    return name, tag

def get_docker_hub_token(repository):
    """Fetch anonymous Bearer token from Docker Hub Auth Service"""
    auth_url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repository}:pull"
    req = urllib.request.Request(auth_url, headers={'User-Agent': 'Socker-Engine/2.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("token")
    except Exception as e:
        print(f"[socker-hub] Auth Token Error: {e}")
        return None

def pull_from_docker_hub(image_tag, target_dir):
    """Pulls layers directly from Docker Hub API v2 and extracts to container root"""
    os.makedirs(target_dir, exist_ok=True)
    repo, tag = parse_image_tag(image_tag)

    print(f"[socker-hub] Resolving Docker Hub Repository: '{repo}' with Tag: '{tag}'...")
    token = get_docker_hub_token(repo)
    if not token:
        print("[socker-hub] Error: Failed to obtain Docker Hub token.")
        return False

    # Fetch Manifest v2
    manifest_url = f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json'
    }

    try:
        req = urllib.request.Request(manifest_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            manifest = json.loads(response.read().decode())
    except Exception as e:
        print(f"[socker-hub] Failed to fetch manifest for {image_tag}: {e}")
        return False

    layers = manifest.get("layers", [])
    if not layers:
        print("[socker-hub] Error: No image layers found in manifest!")
        return False

    print(f"[socker-hub] Found {len(layers)} image layers. Downloading and extracting...")

    # Iterate and extract each layer tarball directly
    for index, layer in enumerate(layers):
        digest = layer.get("digest")
        size_mb = round(layer.get("size", 0) / (1024 * 1024), 2)
        print(f"[socker-hub] Layer [{index + 1}/{len(layers)}]: {digest[:16]}... ({size_mb} MB)")

        layer_url = f"https://registry-1.docker.io/v2/{repo}/blobs/{digest}"
        layer_tar_path = os.path.join(CACHE_DIR, f"{digest.replace('sha256:', '')}.tar.gz")

        # Download Blob layer if not cached
        if not os.path.exists(layer_tar_path):
            try:
                blob_req = urllib.request.Request(layer_url, headers={'Authorization': f'Bearer {token}'})
                with urllib.request.urlopen(blob_req) as resp, open(layer_tar_path, 'wb') as out_file:
                    out_file.write(resp.read())
            except Exception as e:
                print(f"[socker-hub] Error downloading layer {digest}: {e}")
                return False

        # Extract Layer into container root directory
        try:
            with tarfile.open(layer_tar_path, "r:*") as tar:
                tar.extractall(path=target_dir)
        except Exception as e:
            print(f"[socker-hub] Error unpacking layer {digest}: {e}")

    print(f"[socker-hub] Successfully pulled and unpacked '{image_tag}' into {target_dir}!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 2:
        tag = sys.argv[1]
        out_dir = sys.argv[2]
        pull_from_docker_hub(tag, out_dir)
    else:
        print("Usage: python3 socker_image.py <docker_hub_image:tag> <target_directory>")
