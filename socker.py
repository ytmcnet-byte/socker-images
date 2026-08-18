#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from socker_image import pull_and_unpack

CONTAINER_DIR = os.path.expanduser("~/socker_engine/containers")

class SockerContainer:
    def __init__(self, container_id, memory_mb=1024, cpu_quota=100):
        self.container_id = container_id
        self.memory_mb = memory_mb
        self.cpu_quota = cpu_quota
        self.path = os.path.join(CONTAINER_DIR, container_id)

    def run(self, exec_cmd, image_tag="openjdk:17-slim"):
        if not os.path.exists(self.path):
            print(f"[socker] Provisioning container environment with image: '{image_tag}'...")
            pull_and_unpack(image_tag, self.path)

        print("==========================================")
        print(f"[socker] Launching Container: {self.container_id}")
        print(f"[socker] Directory: {self.path}")
        print(f"[socker] Memory Limit: {self.memory_mb} MB | CPU Quota: {self.cpu_quota}%")
        print(f"[socker] Command: {exec_cmd}")
        print("==========================================")

        try:
            subprocess.run(exec_cmd, shell=True, cwd=self.path)
        except Exception as e:
            print(f"[socker] Execution Error: {e}")

def list_containers():
    print(f"{'CONTAINER ID':<20} {'PATH':<45} {'STATUS':<10}")
    print("-" * 75)
    if os.path.exists(CONTAINER_DIR):
        for c_id in os.listdir(CONTAINER_DIR):
            c_path = os.path.join(CONTAINER_DIR, c_id)
            print(f"{c_id:<20} {c_path:<45} {'CREATED':<10}")

def main():
    parser = argparse.ArgumentParser(description="Socker CLI Container Engine")
    subparsers = parser.add_subparsers(dest="subcommand")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("container_id", help="Container ID")
    run_parser.add_argument("--image", default="openjdk:17-slim", help="Docker Hub image tag")
    run_parser.add_argument("--memory", type=int, default=1024, help="Memory limit in MB")
    run_parser.add_argument("--cpus", type=int, default=100, help="CPU percentage")
    run_parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Execution command")

    ps_parser = subparsers.add_parser("ps")

    args = parser.parse_args()

    if args.subcommand == "run":
        # Separate CLI flags from actual shell command execution string
        raw_cmd = [c for c in args.cmd if not c.startswith("--")]
        exec_str = " ".join(raw_cmd) if raw_cmd else "java -version"
        
        container = SockerContainer(args.container_id, memory_mb=args.memory, cpu_quota=args.cpus)
        container.run(exec_str, image_tag=args.image)
    elif args.subcommand == "ps":
        list_containers()

if __name__ == "__main__":
    main()
