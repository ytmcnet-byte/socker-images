#!/usr/bin/env python3
"""
SOCKER DOCKER-HUB DIRECT PULL ENGINE v2.2
Directly fetches and unpacks Docker Hub OCI images without Docker Daemon.
"""

import os
import sys
import json
import tarfile
import urllib.request

CACHE_DIR = os.path.expanduser("~/socker_engine/cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def parse_image_tag(image_tag):
    # GHCR / Pterodactyl Yolks Fallback to Official Docker Hub OpenJDK
    if image_tag.startswith("ghcr.io/") or "pterodactyl" in image_tag:
        return "library/openjdk", "17-slim"

    if ":" in image_tag:
        name, tag = image_tag.split(":", 1)
    else:
        name, tag = image_tag, "latest"

    if "/" not in name:
        name = f"library/{name}"

    if name.startswith("docker.io/"):
        name = name.replace("docker.io/", "")

    return name, tag

def get_docker_hub_token(repository):
    auth_url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repository}:pull"
    req = urllib.request.Request(auth_url, headers={'User-Agent': 'Socker-Engine/2.2'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("token")
    except Exception as e:
        print(f"[socker-hub] Auth Token Error: {e}")
        return None

def pull_from_docker_hub(image_tag, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    repo, tag = parse_image_tag(image_tag)

    print(f"[socker-hub] Resolving Repository: '{repo}' | Tag: '{tag}'...")
    token = get_docker_hub_token(repo)
    if not token:
        print("[socker-hub] Error: Could not obtain auth token from Docker Hub.")
        return False

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
        print(f"[socker-hub] Manifest Error for '{image_tag}': {e}")
        return False

    layers = manifest.get("layers", [])
    if not layers:
        print("[socker-hub] Error: No layers found in image manifest.")
        return False

    print(f"[socker-hub] Found {len(layers)} image layer(s). Downloading & Extracting...")

    for index, layer in enumerate(layers):
        digest = layer.get("digest")
        size_mb = round(layer.get("size", 0) / (1024 * 1024), 2)
        print(f"[socker-hub] Layer [{index + 1}/{len(layers)}]: {digest[:16]}... ({size_mb} MB)")

        layer_url = f"https://registry-1.docker.io/v2/{repo}/blobs/{digest}"
        layer_tar_path = os.path.join(CACHE_DIR, f"{digest.replace('sha256:', '')}.tar.gz")

        if not os.path.exists(layer_tar_path):
            try:
                blob_req = urllib.request.Request(layer_url, headers={'Authorization': f'Bearer {token}'})
                with urllib.request.urlopen(blob_req) as resp, open(layer_tar_path, 'wb') as out_file:
                    out_file.write(resp.read())
            except Exception as e:
                print(f"[socker-hub] Download Error on layer {digest[:16]}: {e}")
                return False

        try:
            with tarfile.open(layer_tar_path, "r:*") as tar:
                tar.extractall(path=target_dir)
        except Exception as e:
            print(f"[socker-hub] Extraction Error on layer {digest[:16]}: {e}")

    print(f"[socker-hub] Successfully extracted '{image_tag}' into {target_dir}")
    return True

# Backwards compatibility alias for socker.py and socker_daemon.py
def pull_and_unpack(image_tag, target_dir):
    return pull_from_docker_hub(image_tag, target_dir)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        pull_and_unpack(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python3 socker_image.py <docker_hub_image:tag> <target_directory>")

