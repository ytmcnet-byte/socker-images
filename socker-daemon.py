#!/usr/bin/env python3
"""
SOCKER DAEMON BRIDGE v1.0
Listens on /tmp/socker.sock and intercepts Pterodactyl Wings API calls
"""

import os
import sys
import json
import socket
import subprocess

SOCKET_PATH = "/tmp/socker.sock"
ENGINE_PATH = os.path.expanduser("~/socker_engine")

def cleanup_socket():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

def handle_client(client_socket):
    try:
        raw_data = client_socket.recv(4096).decode('utf-8')
        if not raw_data:
            return

        print(f"[socker-daemon] Received payload: {raw_data[:100]}...")

        try:
            payload = json.loads(raw_data)
            image_tag = payload.get("Image", "ghcr.io/pterodactyl/yolks:java_21")
            container_id = payload.get("Name", "srv_default").lstrip("/")
            cmd_args = payload.get("Cmd", [])
            exec_cmd = " ".join(cmd_args) if isinstance(cmd_args, list) else str(cmd_args)

            # 1. Pull Image via socker_image.py
            pull_cmd = [sys.executable, os.path.join(ENGINE_PATH, "socker_image.py"), image_tag, os.path.join(ENGINE_PATH, "containers", container_id)]
            subprocess.run(pull_cmd, check=True)

            # 2. Run Container via socker.py
            run_cmd = [sys.executable, os.path.join(ENGINE_PATH, "socker.py"), "run", container_id, "--image", image_tag, exec_cmd]
            subprocess.Popen(run_cmd)

            response = json.dumps({"Id": container_id, "Warnings": []})
            http_response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(response)}\r\n\r\n{response}"
            client_socket.sendall(http_response.encode('utf-8'))

        except json.JSONDecodeError:
            http_response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 15\r\n\r\n{\"status\":\"OK\"}"
            client_socket.sendall(http_response.encode('utf-8'))

    except Exception as e:
        print(f"[socker-daemon] Error handling request: {e}")
    finally:
        client_socket.close()

def start_daemon():
    cleanup_socket()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o777)
    server.listen(5)

    print("==========================================")
    print(f"[socker-daemon] Listening on {SOCKET_PATH}...")
    print("==========================================")

    try:
        while True:
            client, _ = server.accept()
            handle_client(client)
    except KeyboardInterrupt:
        print("\n[socker-daemon] Stopping daemon...")
    finally:
        cleanup_socket()

if __name__ == "__main__":
    start_daemon()

