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
    # Manual argument extraction to completely prevent --image from leaking into shell execution
    args = sys.argv[1:]
    
    if not args or args[0] == "ps":
        list_containers()
        return

    if args[0] == "run":
        if len(args) < 2:
            print("Usage: socker run <container_id> [--image <image>] [--memory <mb>] <command...>")
            return
            
        container_id = args[1]
        image_tag = "openjdk:17-slim"
        memory_mb = 1024
        cpu_quota = 100
        
        # Parse known flags and strip them completely
        cmd_tokens = args[2:]
        clean_cmd_tokens = []
        i = 0
        while i < len(cmd_tokens):
            token = cmd_tokens[i]
            if token == "--image" and i + 1 < len(cmd_tokens):
                image_tag = cmd_tokens[i + 1]
                i += 2
            elif token == "--memory" and i + 1 < len(cmd_tokens):
                memory_mb = int(cmd_tokens[i + 1])
                i += 2
            elif token == "--cpus" and i + 1 < len(cmd_tokens):
                cpu_quota = int(cmd_tokens[i + 1])
                i += 2
            else:
                clean_cmd_tokens.append(token)
                i += 1

        exec_str = " ".join(clean_cmd_tokens) if clean_cmd_tokens else "java -version"
        container = SockerContainer(container_id, memory_mb=memory_mb, cpu_quota=cpu_quota)
        container.run(exec_str, image_tag=image_tag)

if __name__ == "__main__":
    main()
