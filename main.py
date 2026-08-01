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


def _wait_for_api(host: str, port: int, timeout: float = 15.0) -> bool:
    """Poll /health until the API answers. A fixed sleep races on slow starts."""
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout
    url = f"http://{host}:{port}/health"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.25)
    return False


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

    if not _wait_for_api(host, port):
        print(
            f"Warning: API server did not respond on http://{host}:{port} — "
            "the UI will start but every request will fail."
        )

    print(f"n8n Workflow Agent starting — API: http://{host}:{port}")

    # Launch Flet WEB app (opens in the browser) in the main thread
    from src.ui.app import run_flet_app

    run_flet_app()


if __name__ == "__main__":
    main()
