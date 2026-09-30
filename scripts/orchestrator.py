#!/usr/bin/env python3
"""
Kandezhuthu AI - App Orchestrator CLI

Unified CLI to start, stop, check status, and orchestrate automated demo video
recording sessions for Kandezhuthu AI.

Usage:
    uv run python scripts/orchestrator.py start [--port 8081] [--daemon]
    uv run python scripts/orchestrator.py stop
    uv run python scripts/orchestrator.py status
    uv run python scripts/orchestrator.py record [--pace cinematic] [--port 8081]
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.orchestrator import AppOrchestrator, get_stored_pid, stop_stored_instance


def main():
    parser = argparse.ArgumentParser(
        description="Kandezhuthu AI Orchestrator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Start
    start_parser = subparsers.add_parser("start", help="Start the Kandezhuthu server")
    start_parser.add_argument("--port", type=int, default=8081, help="Port to bind (default: 8081)")
    start_parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    start_parser.add_argument("--daemon", action="store_true", help="Run detached in background")

    # Stop
    subparsers.add_parser("stop", help="Stop running Kandezhuthu server")

    # Status
    status_parser = subparsers.add_parser("status", help="Query server health and PID")
    status_parser.add_argument("--port", type=int, default=8081, help="Port to check (default: 8081)")
    status_parser.add_argument("--host", default="127.0.0.1", help="Host to check (default: 127.0.0.1)")

    # Record Demo
    record_parser = subparsers.add_parser("record", help="Orchestrate server and record demo video")
    record_parser.add_argument("--port", type=int, default=8081, help="Target port (default: 8081)")
    record_parser.add_argument("--host", default="127.0.0.1", help="Target host (default: 127.0.0.1)")
    record_parser.add_argument("--pace", choices=["cinematic", "normal", "fast"], default="cinematic", help="Pacing")
    record_parser.add_argument("--output-dir", default=None, help="Custom output directory")
    record_parser.add_argument("--keep-server", action="store_true", help="Keep server running after recording")

    args = parser.parse_args()

    if args.command == "start":
        orch = AppOrchestrator(host=args.host, port=args.port, reuse_existing=True)
        orch.start()
        if not args.daemon:
            print("[Orchestrator] Server is active. Press Ctrl+C to terminate.")
            try:
                import time
                while True:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                print("\n[Orchestrator] Interrupted.")
            finally:
                orch.stop()

    elif args.command == "stop":
        stopped = stop_stored_instance()
        if not stopped:
            print("[Orchestrator] No tracked instance was running.")

    elif args.command == "status":
        orch = AppOrchestrator(host=args.host, port=args.port)
        healthy = orch.is_healthy()
        pid = get_stored_pid()
        status_text = "ONLINE (HEALTHY) 🟢" if healthy else "OFFLINE 🔴"
        print(f"Kandezhuthu Server: {status_text}")
        print(f"Target URL:         {orch.base_url}")
        if pid:
            print(f"Process PID:        {pid}")

    elif args.command == "record":
        from tests.fixtures.tools.record_demo import OUTPUT_DIR, DemoVideoRecorder, transcode_video

        out_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
        orch = AppOrchestrator(host=args.host, port=args.port, reuse_existing=True)
        orch.start()

        try:
            recorder = DemoVideoRecorder(base_url=orch.base_url, output_dir=out_dir, pace=args.pace)
            raw_video = recorder.record_journey()
            transcode_video(raw_video, out_dir)
            print("\n✔ Demo video successfully orchestrated and created!")
        finally:
            if not args.keep_server:
                orch.stop()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
