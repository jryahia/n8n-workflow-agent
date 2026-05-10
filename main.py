"""
Entry point — starts the FastAPI server in a background thread and launches the Flet UI.
Pass --api-only to run only the API server (for Docker deployment).
"""

import argparse
import asyncio
import sys
import threading
import time


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="n8n Workflow Agent")
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Run only the FastAPI server without the Flet desktop UI",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Override API host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Override API port",
    )
    return parser.parse_args()


def start_api_server(host: str, port: int) -> None:
    """Start uvicorn in a daemon thread (or blocking if api-only)."""
    import uvicorn
    from src.api_server import app

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="warning",
        loop="asyncio",
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


def main() -> None:
    args = _parse_args()

    from src.config import settings

    host = args.host or settings.api_host
    port = args.port or settings.api_port

    if args.api_only:
        print(f"Starting n8n Workflow Agent API on http://{host}:{port}")
        start_api_server(host, port)
        return

    # Launch API server in background thread
    api_thread = threading.Thread(
        target=start_api_server,
        args=(host, port),
        daemon=True,
        name="api-server",
    )
    api_thread.start()

    # Give the server a moment to start
    time.sleep(1.5)

    print(f"n8n Workflow Agent starting — API: http://{host}:{port}")

    # Launch Flet desktop app in main thread
    from src.ui.app import run_flet_app

    run_flet_app()


if __name__ == "__main__":
    main()
