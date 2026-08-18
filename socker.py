#!/usr/bin/env python3
"""
SOCKER CORE ENGINE v3.0
Non-Root Container Executor with CPU Time-Slicing & Memory Enforcement
"""

import os
import sys
import time
import signal
import psutil
import argparse
import subprocess
from socker_image import pull_and_unpack

BASE_DIR = os.path.expanduser("~/socker_engine")
CONTAINERS_DIR = os.path.join(BASE_DIR, "containers")

os.makedirs(CONTAINERS_DIR, exist_ok=True)

class SockerContainer:
    def __init__(self, container_id, memory_mb=1024, cpu_quota=100):
        self.container_id = container_id
        self.memory_mb = memory_mb
        self.cpu_quota = cpu_quota  # 10 to 100 percent
        self.container_path = os.path.join(CONTAINERS_DIR, container_id)
        os.makedirs(self.container_path, exist_ok=True)

    def monitor_cpu(self, process):
        """CPU Time-Slicing loop using SIGSTOP and SIGCONT for non-root cgroup alternative"""
        quota_decimal = self.cpu_quota / 100.0
        if quota_decimal >= 1.0:
            return  # No throttling needed for 100%

        slice_time = 0.1  # 100ms cycle
        run_time = slice_time * quota_decimal
        sleep_time = slice_time - run_time

        try:
            while process.poll() is None:
                time.sleep(run_time)
                if process.poll() is None:
                    os.kill(process.pid, signal.SIGSTOP)
                    time.sleep(sleep_time)
                    os.kill(process.pid, signal.SIGCONT)
        except (ProcessLookupError, KeyboardInterrupt):
            pass

    def run(self, exec_command, image_tag=None):
        """Prepares environment and launches process"""
        if image_tag:
            print(f"[socker] Ensuring image tag '{image_tag}' is provisioned...")
            pull_and_unpack(image_tag, self.container_path)

        # Environment Binaries (Isolated Java / Node / Python)
        local_bin = os.path.join(self.container_path, "bin")
        env = os.environ.copy()
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"

        # Inject Memory limits for Java Runtimes (-Xmx)
        final_cmd = exec_command
        if "java" in exec_command and "-Xmx" not in exec_command:
            final_cmd = f"java -Xmx{self.memory_mb}M " + exec_command.replace("java", "", 1)

        print(f"==========================================")
        print(f"[socker] Launching Container: {self.container_id}")
        print(f"[socker] Directory: {self.container_path}")
        print(f"[socker] Memory Limit: {self.memory_mb} MB | CPU Quota: {self.cpu_quota}%")
        print(f"[socker] Command: {final_cmd}")
        print(f"==========================================")

        try:
            # Spawn process in container directory
            process = subprocess.Popen(
                final_cmd,
                shell=True,
                cwd=self.container_path,
                env=env,
                preexec_fn=os.setsid
            )

            # Start CPU Throttle Thread
            import threading
            cpu_thread = threading.Thread(target=self.monitor_cpu, args=(process,), daemon=True)
            cpu_thread.start()

            # Wait for container execution
            process.wait()

        except Exception as e:
            print(f"[socker] Container execution error: {e}")

def list_containers():
    print(f"{'CONTAINER ID':<20} {'PATH':<45} {'STATUS'}")
    print("-" * 75)
    if not os.path.exists(CONTAINERS_DIR):
        return
    for c_id in os.listdir(CONTAINERS_DIR):
        c_path = os.path.join(CONTAINERS_DIR, c_id)
        if os.path.isdir(c_path):
            print(f"{c_id:<20} {c_path:<45} Exited/Idle")

def main():
    parser = argparse.ArgumentParser(description="Socker Non-Root Container CLI Engine")
    subparsers = parser.add_subparsers(dest="subcommand")

    # Run Command
    run_parser = subparsers.add_parser("run", help="Run a container")
    run_parser.add_argument("container_id", help="Container Unique Identifier")
    run_parser.add_argument("--image", help="GitHub Registry Image Tag", default="ghcr.io/pterodactyl/yolks:java_21")
    run_parser.add_argument("--memory", help="Memory limit in MB", type=int, default=1024)
    run_parser.add_argument("--cpus", help="CPU Limit Percentage (10-100)", type=int, default=100)
    run_parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Execution command")

    # List Command
    subparsers.add_parser("ps", help="List active/built containers")

    args = parser.parse_args()

    if args.subcommand == "run":
        exec_str = " ".join(args.cmd) if args.cmd else "java -version"
        container = SockerContainer(args.container_id, memory_mb=args.memory, cpu_quota=args.cpus)
        container.run(exec_str, image_tag=args.image)
    elif args.subcommand == "ps":
        list_containers()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

