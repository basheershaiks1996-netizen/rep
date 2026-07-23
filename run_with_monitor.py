"""
Launches the uvicorn server and monitors for VS Code process.
When VS Code is closed, the server is automatically terminated.
"""

import subprocess
import time
import sys
import os
import signal

# psutil is imported dynamically inside main() / functions to allow
# auto-installation on first run.

UVICORN_ARGS = [
    sys.executable, "-m", "uvicorn", "backend.main:app",
    "--reload", "--host", "127.0.0.1", "--port", "8000"
]

VS_CODE_PROCESS_NAMES = ["code.exe", "Code.exe"]


def find_vscode_processes(psutil):
    """Return a list of psutil Process objects for all running VS Code instances."""
    vscode_procs = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] in VS_CODE_PROCESS_NAMES:
                vscode_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return vscode_procs


def wait_for_vscode_start(psutil):
    """
    Wait up to 30 seconds for at least one VS Code instance to appear.
    Return the set of VS Code PIDs found.
    """
    print("[monitor] Waiting for VS Code to start (up to 30s)...")
    for attempt in range(60):
        procs = find_vscode_processes(psutil)
        if procs:
            pids = {p.info["pid"] for p in procs}
            print(f"[monitor] Detected VS Code running (PIDs: {pids})")
            return pids
        time.sleep(0.5)
    print("[monitor] Warning: No VS Code process detected. Monitoring will stop.")
    return set()


def monitor_vscode(known_pids, psutil):
    """
    Poll until all known VS Code PIDs are gone.
    Returns True if VS Code exitted (monitoring stopped).
    """
    print("[monitor] Monitoring VS Code process. Close VS Code to stop the server.")
    while True:
        still_running = []
        for pid in list(known_pids):
            try:
                proc = psutil.Process(pid)
                if proc.name() in VS_CODE_PROCESS_NAMES:
                    still_running.append(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process no longer exists — VS Code was closed.
                pass
        known_pids.clear()
        known_pids.update(still_running)

        if not known_pids:
            print("[monitor] VS Code has been closed. Shutting down server...")
            return True

        time.sleep(1)


def main():
    # Ensure psutil is installed
    try:
        import psutil
    except ImportError:
        print("Required package 'psutil' is missing. Installing...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "psutil"]
        )
        import psutil

    print(f"[monitor] Starting uvicorn: {' '.join(UVICORN_ARGS)}")
    uvicorn_proc = subprocess.Popen(
        UVICORN_ARGS,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    try:
        known_pids = wait_for_vscode_start(psutil)
        if not known_pids:
            # Fall back: if VS Code was never detected, just keep
            # the server running and let user manually Ctrl+C.
            print("[monitor] No VS Code found; server will run until Ctrl+C is pressed.")
            uvicorn_proc.wait()
            return

        # Wait for uvicorn to be ready, then open in VS Code's built-in browser
        time.sleep(2)
        print("[monitor] Opening http://127.0.0.1:8000 in VS Code's built-in browser...")
        subprocess.Popen(
            ["code", "--open-url", "http://127.0.0.1:8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        monitor_vscode(known_pids, psutil)
    finally:
        # Terminate the uvicorn process
        print("[monitor] Terminating uvicorn server...")
        if uvicorn_proc.poll() is None:
            # Try graceful shutdown first
            if sys.platform == "win32":
                os.kill(uvicorn_proc.pid, signal.CTRL_BREAK_EVENT)
                time.sleep(2)
            uvicorn_proc.terminate()
            try:
                uvicorn_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                uvicorn_proc.kill()
                uvicorn_proc.wait()
        print("[monitor] Server stopped.")


if __name__ == "__main__":
    main()