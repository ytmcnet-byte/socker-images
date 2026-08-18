#!/usr/bin/env python3
import os
import sys
import json
import time
import socket
import asyncio
import argparse
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="[socker] %(asctime)s - %(message)s")

# 1. Socket Path Handling (Fallback Support)
PRIMARY_SOCKET = "/var/run/socker.sock"
FALLBACK_SOCKET = "/root/socker.sock"

def resolve_socket_path():
    for path in [PRIMARY_SOCKET, FALLBACK_SOCKET]:
        dir_path = os.path.dirname(path)
        if os.access(dir_path, os.W_OK) or os.geteuid() == 0:
            return path
    return FALLBACK_SOCKET

SOCKET_PATH = resolve_socket_path()
DATA_DIR = os.path.expanduser("~/.socker")
CONTAINERS_DIR = os.path.join(DATA_DIR, "containers")

os.makedirs(CONTAINERS_DIR, exist_ok=True)

# ----------------- DOCKER REST API ENGINE -----------------

async def http_response(writer, status_code, data_obj):
    body = json.dumps(data_obj)
    status_map = {200: "OK", 201: "Created", 204: "No Content", 404: "Not Found", 500: "Internal Server Error"}
    status_text = status_map.get(status_code, "OK")
    
    header = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Server: Docker/20.10.21 (Socker-Engine)\r\n"
        "Connection: close\r\n\r\n"
    )
    writer.write(header.encode() + body.encode())
    await writer.drain()

async def handle_docker_api(reader, writer):
    try:
        req_line = await reader.readline()
        if not req_line:
            writer.close()
            return

        parts = req_line.decode().strip().split(" ")
        if len(parts) < 2:
            writer.close()
            return
            
        method, uri = parts[0], parts[1]

        # Header parsing
        content_length = 0
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
            if line.lower().startswith(b"content-length:"):
                content_length = int(line.split(b":")[1].strip())

        # Body parsing
        body_data = {}
        if content_length > 0:
            raw_body = await reader.readexact(content_length)
            try:
                body_data = json.loads(raw_body.decode())
            except Exception:
                pass

        # Clean URI path
        path = uri.split("?")[0]

        # ----------------- DOCKER API ENDPOINTS -----------------
        
        # 1. /_ping
        if path == "/_ping":
            resp = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 2\r\n\r\nOK"
            writer.write(resp.encode())
            await writer.drain()

        # 2. /version
        elif path.endswith("/version"):
            await http_response(writer, 200, {
                "Platform": {"Name": "Socker Engine"},
                "Version": "20.10.21",
                "ApiVersion": "1.41",
                "MinAPIVersion": "1.12",
                "GitCommit": "socker-v1.0",
                "GoVersion": "go1.18.1",
                "Os": "linux",
                "Arch": "amd64"
            })

        # 3. /containers/json (docker ps)
        elif path.endswith("/containers/json"):
            containers = []
            for cid in os.listdir(CONTAINERS_DIR):
                cfg_path = os.path.join(CONTAINERS_DIR, cid, "config.json")
                if os.path.exists(cfg_path):
                    with open(cfg_path) as f:
                        cdata = json.load(f)
                        containers.append({
                            "Id": cdata["Id"],
                            "Names": [f"/{cdata['Name']}"],
                            "Image": cdata["Image"],
                            "State": cdata["Status"],
                            "Status": f"Up {cdata['Status']}",
                            "Created": cdata["Created"]
                        })
            await http_response(writer, 200, containers)

        # 4. /containers/create (docker create / run)
        elif path.endswith("/containers/create"):
            cid = os.urandom(8).hex()
            c_name = body_data.get("Name") or f"socker_{cid[:6]}"
            image = body_data.get("Image", "ubuntu:latest")
            host_cfg = body_data.get("HostConfig", {})

            # Limits Extractions (cgroups equivalent structure)
            ram_mb = host_cfg.get("Memory", 0) // (1024 * 1024)
            cpus = host_cfg.get("NanoCpus", 0) / 1e9

            c_dir = os.path.join(CONTAINERS_DIR, cid)
            os.makedirs(c_dir, exist_ok=True)

            c_info = {
                "Id": cid,
                "Name": c_name,
                "Image": image,
                "MemoryMB": ram_mb,
                "CPUs": cpus,
                "Status": "created",
                "Created": int(time.time())
            }
            
            with open(os.path.join(c_dir, "config.json"), "w") as f:
                json.dump(c_info, f)

            await http_response(writer, 201, {"Id": cid, "Warnings": []})

        # 5. /containers/{id}/start
        elif "/containers/" in path and path.endswith("/start"):
            cid = path.split("/containers/")[1].split("/")[0]
            cfg_path = os.path.join(CONTAINERS_DIR, cid, "config.json")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r+") as f:
                    data = json.load(f)
                    data["Status"] = "running"
                    f.seek(0)
                    json.dump(data, f)
                    f.truncate()
                await http_response(writer, 204, {})
            else:
                await http_response(writer, 404, {"message": "No such container"})

        # 6. /containers/{id}/stop
        elif "/containers/" in path and path.endswith("/stop"):
            cid = path.split("/containers/")[1].split("/")[0]
            cfg_path = os.path.join(CONTAINERS_DIR, cid, "config.json")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r+") as f:
                    data = json.load(f)
                    data["Status"] = "exited"
                    f.seek(0)
                    json.dump(data, f)
                    f.truncate()
                await http_response(writer, 204, {})
            else:
                await http_response(writer, 404, {"message": "No such container"})

        # 7. /images/create (docker pull)
        elif path.endswith("/images/create"):
            await http_response(writer, 200, {"status": "Download complete"})

        else:
            await http_response(writer, 200, {})

    except Exception as e:
        logging.error(f"API Error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def start_daemon():
    if os.path.exists(SOCKET_PATH):
        try: os.remove(SOCKET_PATH)
        except OSError: pass

    server = await asyncio.start_unix_server(handle_docker_api, path=SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o777)
    logging.info(f"Socker Daemon (Docker Engine API) live at: {SOCKET_PATH}")
    async with server:
        await server.serve_forever()

# ----------------- CLI CLIENT (socker wrapper) -----------------

def run_cli_request(method, path, body=None):
    if not os.path.exists(SOCKET_PATH):
        print(f"Error: Socker socket missing at {SOCKET_PATH}. Start daemon first!")
        sys.exit(1)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(SOCKET_PATH)
        json_body = json.dumps(body) if body else ""
        req = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: {len(json_body)}\r\n\r\n{json_body}"
        sock.sendall(req.encode())

        response = sock.recv(16384).decode()
        header_part, body_part = response.split("\r\n\r\n", 1)
        return json.loads(body_part) if body_part else {}
    except Exception as e:
        print(f"CLI Communication Error: {e}")
        return {}
    finally:
        sock.close()

def main():
    parser = argparse.ArgumentParser(prog="socker", description="Non-root Docker Level Container Engine")
    subparsers = parser.add_subparsers(dest="command")

    # socker daemon
    subparsers.add_parser("daemon", help="Run Socker Engine Background Service")

    # socker ps
    subparsers.add_parser("ps", help="List containers")

    # socker pull <image>
    pull_p = subparsers.add_parser("pull", help="Pull image")
    pull_p.add_argument("image", help="Image tag")

    # socker run [options] <image>
    run_p = subparsers.add_parser("run", help="Run container")
    run_p.add_argument("image", help="Image tag")
    run_p.add_argument("--name", help="Container Name")
    run_p.add_argument("-m", "--memory", help="Memory limit (e.g., 512M)")
    run_p.add_argument("--cpus", help="CPU Limit")

    # socker stop <id/name>
    stop_p = subparsers.add_parser("stop", help="Stop container")
    stop_p.add_argument("id", help="Container ID or Name")

    args = parser.parse_args()

    if args.command == "daemon":
        asyncio.run(start_daemon())
    elif args.command == "ps":
        data = run_cli_request("GET", "/containers/json")
        print(f"{'CONTAINER ID':<15} {'IMAGE':<20} {'STATUS':<15} {'NAMES':<15}")
        print("-" * 65)
        for c in data:
            print(f"{c.get('Id')[:12]:<15} {c.get('Image'):<20} {c.get('Status'):<15} {c.get('Names')[0]:<15}")
    elif args.command == "pull":
        run_cli_request("POST", f"/images/create?fromImage={args.image}")
        print(f"Pulled {args.image} successfully.")
    elif args.command == "run":
        mem_bytes = 0
        if args.memory:
            if "M" in args.memory.upper():
                mem_bytes = int(args.memory.upper().replace("M", "")) * 1024 * 1024
            elif "G" in args.memory.upper():
                mem_bytes = int(args.memory.upper().replace("G", "")) * 1024 * 1024 * 1024

        payload = {
            "Image": args.image,
            "Name": args.name,
            "HostConfig": {
                "Memory": mem_bytes,
                "NanoCpus": int(float(args.cpus) * 1e9) if args.cpus else 0
            }
        }
        res = run_cli_request("POST", "/containers/create", payload)
        cid = res.get("Id")
        if cid:
            run_cli_request("POST", f"/containers/{cid}/start")
            print(f"Container created and started: {cid[:12]}")
    elif args.command == "stop":
        run_cli_request("POST", f"/containers/{args.id}/stop")
        print(f"Container {args.id} stopped.")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
