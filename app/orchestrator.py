"""Kandezhuthu AI App Orchestrator.

Provides robust process lifecycle management, automated startup, health checking,
and graceful shutdown for the Kandezhuthu AI FastAPI backend and web UI.

Usable as:
1. A Python context manager:
    with AppOrchestrator(port=8081) as orch:
        ...  # do work while server is guaranteed healthy
2. A CLI tool:
    uv run python -m app.orchestrator start --port 8081
    uv run python -m app.orchestrator status
    uv run python -m app.orchestrator stop
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORT = int(os.environ.get("PORT", "8081"))
DEFAULT_HOST = os.environ.get("HOST", "127.0.0.1")
PID_FILE = REPO_ROOT / ".orchestrator.pid"
LOG_DIR = REPO_ROOT / "logs"


class AppOrchestrator:
    """Manages the startup, health-checking, and shutdown of the Kandezhuthu AI server."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        startup_timeout: float = 30.0,
        log_file: Optional[Path] = None,
        reuse_existing: bool = True,
    ):
        self.host = host
        self.port = port
        self.startup_timeout = startup_timeout
        self.log_file = log_file or (LOG_DIR / "orchestrator_server.log")
        self.reuse_existing = reuse_existing
        self.process: Optional[subprocess.Popen] = None
        self.is_managed_process = False

    @property
    def base_url(self) -> str:
        """Returns the base URL for the orchestrated app."""
        return f"http://{self.host}:{self.port}"

    def is_healthy(self, timeout: float = 1.5) -> bool:
        """Checks if the Kandezhuthu server is responding to health checks."""
        for endpoint in ["/health", "/api/config", "/"]:
            url = f"{self.base_url}{endpoint}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Kandezhuthu-Orchestrator/1.0"})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.status in (200, 204):
                        return True
            except Exception:
                continue
        return False

    def start(self) -> "AppOrchestrator":
        """Starts the server or connects to an existing healthy instance."""
        if self.reuse_existing and self.is_healthy():
            print(f"[Orchestrator] Existing healthy Kandezhuthu instance detected at {self.base_url}")
            return self

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["PORT"] = str(self.port)
        env["HOST"] = str(self.host)
        env["PYTHONUNBUFFERED"] = "1"

        print(f"[Orchestrator] Launching Kandezhuthu AI server on {self.base_url}...")
        log_handle = open(self.log_file, "a", encoding="utf-8")

        # Launch uvicorn via python executable to ensure venv / uv environment is preserved
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "frontend.main:app",
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--log-level",
            "info",
        ]

        self.process = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=env,
            preexec_fn=os.setsid if sys.platform != "win32" else None,
        )
        self.is_managed_process = True

        # Write PID file for process tracking
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(f"{self.process.pid}\n{self.port}\n")
        except Exception as e:
            print(f"[Orchestrator] Warning: could not write PID file: {e}")

        # Wait for server readiness
        self.wait_until_ready()
        print(f"[Orchestrator] Server successfully orchestrated & ready at {self.base_url}")
        return self

    def wait_until_ready(self) -> None:
        """Polls the server until it responds or timeout occurs."""
        start_time = time.time()
        poll_interval = 0.4
        print(f"[Orchestrator] Waiting for health status at {self.base_url} (timeout: {self.startup_timeout}s)...")

        while time.time() - start_time < self.startup_timeout:
            if self.process and self.process.poll() is not None:
                ret = self.process.poll()
                raise RuntimeError(
                    f"[Orchestrator] Server process exited prematurely with code {ret}. Check log: {self.log_file}"
                )

            if self.is_healthy():
                return
            time.sleep(poll_interval)

        raise TimeoutError(
            f"[Orchestrator] Server at {self.base_url} failed to respond within {self.startup_timeout}s."
        )

    def stop(self) -> None:
        """Gracefully terminates the server process."""
        if not self.is_managed_process or not self.process:
            return

        print(f"[Orchestrator] Stopping Kandezhuthu server (PID {self.process.pid})...")
        try:
            if sys.platform != "win32":
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            else:
                self.process.terminate()

            # Wait up to 5 seconds for clean exit
            try:
                self.process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                print("[Orchestrator] Process did not terminate within 5s, sending SIGKILL...")
                if sys.platform != "win32":
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                else:
                    self.process.kill()
                self.process.wait()
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"[Orchestrator] Notice while terminating process: {e}")
        finally:
            self.process = None
            self.is_managed_process = False
            if PID_FILE.exists():
                try:
                    PID_FILE.unlink()
                except Exception:
                    pass
            print("[Orchestrator] Server stopped successfully.")

    def __enter__(self) -> "AppOrchestrator":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


def get_stored_pid() -> Optional[int]:
    """Retrieves stored PID from PID file if available."""
    if not PID_FILE.exists():
        return None
    try:
        lines = PID_FILE.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            return int(lines[0])
    except Exception:
        pass
    return None


def stop_stored_instance() -> bool:
    """Stops any previously tracked server process."""
    pid = get_stored_pid()
    if not pid:
        return False
    try:
        print(f"[Orchestrator] Terminating previous process PID {pid}...")
        if sys.platform != "win32":
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
        time.sleep(1.0)
    except ProcessLookupError:
        pass
    except Exception as e:
        print(f"[Orchestrator] Could not stop PID {pid}: {e}")
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Kandezhuthu AI App Orchestrator")
    subparsers = parser.add_subparsers(dest="action", help="Orchestration action")

    # Start
    start_parser = subparsers.add_parser("start", help="Start the server")
    start_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind (default: 8081)")
    start_parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind (default: 127.0.0.1)")
    start_parser.add_argument("--daemon", action="store_true", help="Leave running in background")

    # Stop
    subparsers.add_parser("stop", help="Stop any running orchestrated instance")

    # Status
    status_parser = subparsers.add_parser("status", help="Check server health status")
    status_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to check")
    status_parser.add_argument("--host", default=DEFAULT_HOST, help="Host to check")

    args = parser.parse_args()

    if args.action == "start":
        orch = AppOrchestrator(host=args.host, port=args.port, reuse_existing=True)
        orch.start()
        if not args.daemon:
            print("[Orchestrator] Server running. Press Ctrl+C to terminate.")
            try:
                while True:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                print("\n[Orchestrator] Interrupted by user.")
            finally:
                orch.stop()
    elif args.action == "stop":
        stopped = stop_stored_instance()
        if not stopped:
            print("[Orchestrator] No tracked process PID found.")
    elif args.action == "status":
        orch = AppOrchestrator(host=args.host, port=args.port)
        healthy = orch.is_healthy()
        pid = get_stored_pid()
        status_str = "HEALTHY (ONLINE)" if healthy else "OFFLINE"
        print(f"Kandezhuthu AI Server Status: {status_str}")
        print(f"Target URL: {orch.base_url}")
        if pid:
            print(f"Tracked PID: {pid}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
