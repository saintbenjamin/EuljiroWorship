# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/EuljiroWorship.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Main entry point for the EuljiroWorship application.

This module launches the `Qt <https://doc.qt.io/qt-6/index.html>`_-based Slide Generator UI and starts the background
servers required for the browser-based overlay:

- An HTTP server (static file hosting; default: port ``8080``)
- A `WebSocket <https://websocket-client.readthedocs.io/en/latest/index.html>`_ server (real-time slide updates; default: port ``8765``)

Typical usage::

    python EuljiroWorship.py

Note:
    - The HTTP document root is currently set to the project root directory. If your overlay/static files live under a specific subdirectory (e.g. ``web/``), update ``http_cwd`` accordingly.
    - Both servers are started as subprocesses. They are terminated on normal `Qt <https://doc.qt.io/qt-6/index.html>`_ exit and also via ``atexit`` as a fallback.
    - Alternate launcher modes (controller / HTTP server / WebSocket server / interruptor) are exposed so the same entry point can be reused in frozen executable builds.
    - If the server subprocess exits immediately (e.g., port already in use), the launcher raises a ``RuntimeError``.
"""

import atexit
import argparse
import subprocess
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

from core.config import paths
from core.utils.runtime_launcher import (
    build_entry_command,
    ensure_runtime_cwd,
    get_runtime_base_dir,
    set_windows_app_user_model_id,
)

def _project_root() -> Path:
    """
    Return the project root directory.

    In source execution, this resolves to the repository root.
    In frozen execution, this resolves to the directory containing the
    bundled executable and its staged resource folders.

    Returns:
        pathlib.Path:
            Absolute path to the project root directory.
    """
    return get_runtime_base_dir()

def _start_http_server(cwd: Path, port: int = 8080) -> subprocess.Popen:
    """
    Start the static-file HTTP server as a subprocess.

    The subprocess relaunches the main application entry point in dedicated
    ``--http-server`` mode so the same implementation works in both source
    and frozen executable builds.

    Args:
        cwd (pathlib.Path):
            The directory to serve as the HTTP document root (process working directory).
        port (int, optional):
            TCP port to bind the HTTP server to. Default is ``8080``.

    Returns:
        subprocess.Popen:
            A handle to the spawned HTTP server process.

    Note:
        - ``start_new_session=True`` is used to improve shutdown reliability across platforms by detaching the child process session.
        - Standard output/error are inherited by default (``stdout=None``, ``stderr=None``).

    """
    cmd = build_entry_command("--http-server", "--root", str(cwd), "--port", str(port))
    return subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=None,
        stderr=None,
        text=True,
        start_new_session=True,  # Improves shutdown reliability across platforms
    )

def _start_ws_server(root: Path) -> subprocess.Popen:
    """
    Start the `WebSocket <https://websocket-client.readthedocs.io/en/latest/index.html>`_ server as a subprocess.

    The subprocess relaunches the main application entry point in dedicated
    ``--ws-server`` mode so the same launcher path works in both source
    and frozen executable builds.

    Args:
        root (pathlib.Path):
            Absolute path to the project root directory.

    Returns:
        subprocess.Popen:
            A handle to the spawned `WebSocket <https://websocket-client.readthedocs.io/en/latest/index.html>`_ server process.

    Note:
        - The process is spawned with its working directory set to the project root.
        - ``start_new_session=True`` is used to improve shutdown reliability across platforms.
    """
    cmd = build_entry_command("--ws-server", "--port", "8765")
    return subprocess.Popen(
        cmd,
        cwd=str(root),
        stdout=None,
        stderr=None,
        text=True,
        start_new_session=True,  # Improves shutdown reliability across platforms
    )

def _terminate_process(p: subprocess.Popen) -> None:
    """
    Terminate a subprocess gracefully, with a forced kill as fallback.

    This function attempts a soft shutdown first using ``terminate()``, then
    waits briefly. If the process does not exit within the timeout, it escalates
    to ``kill()``. Any exceptions during shutdown are suppressed intentionally
    (shutdown paths should not crash the main application).

    Args:
        p (subprocess.Popen):
            Subprocess handle to terminate. If the process is already exited, this function does nothing.

    Returns:
        None
    """
    if p is None:
        return

    try:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                p.kill()
    except Exception:
        # Intentionally suppress all exceptions during shutdown
        pass

def _ensure_alive(p: subprocess.Popen, name: str) -> None:
    """
    Verify that a freshly spawned subprocess is still running.

    This is a small safety check to catch immediate failures such as:

    - address/port already in use
    - missing dependencies
    - import/runtime errors causing instant exit

    The function waits briefly and then checks the return code via ``poll()``.
    If the process has already exited, a ``RuntimeError`` is raised.

    Args:
        p (subprocess.Popen):
            Subprocess handle to validate.
        name (str):
            Human-readable process name used in the error message.

    Raises:
        RuntimeError:
            If the subprocess has already exited.

    Returns:
        None
    """
    time.sleep(0.25)
    rc = p.poll()
    if rc is not None:
        raise RuntimeError(f"{name} exited immediately (return code: {rc}).")

def _restart_process_if_needed(
    p: subprocess.Popen | None,
    name: str,
    starter,
) -> subprocess.Popen | None:
    """
    Restart a background subprocess if it exited unexpectedly.

    Args:
        p (subprocess.Popen | None):
            Current subprocess handle.
        name (str):
            Human-readable process name for status output.
        starter (Callable[[], subprocess.Popen]):
            Zero-argument factory that starts a replacement subprocess.

    Returns:
        subprocess.Popen | None:
            The still-running original process, a newly restarted process,
            or the original handle if restart failed.
    """
    if p is None or p.poll() is None:
        return p

    print(f"[!] {name} exited unexpectedly (return code: {p.returncode}). Restarting...")

    try:
        new_process = starter()
        _ensure_alive(new_process, name)
        print(f"[i] {name} restarted successfully.")
        return new_process
    except Exception as e:
        print(f"[x] Failed to restart {name}: {e}")
        return p

def _parse_mode_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse launcher mode arguments.

    Args:
        argv (list[str] | None):
            Optional explicit argument list. If None, ``sys.argv[1:]`` is used.

    Returns:
        argparse.Namespace:
            Parsed launcher arguments.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--controller", action="store_true")
    parser.add_argument("--interruptor", action="store_true")
    parser.add_argument("--ws-server", action="store_true")
    parser.add_argument("--http-server", action="store_true")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--root", default=None)
    return parser.parse_args(argv)

def _run_static_http_server(root: Path, port: int = 8080) -> None:
    """
    Run a static-file HTTP server in the current process.

    Args:
        root (pathlib.Path):
            Directory to expose as the HTTP document root.
        port (int, optional):
            TCP port to bind. Defaults to ``8080``.

    Returns:
        None
    """
    class QuietStaticHandler(SimpleHTTPRequestHandler):
        """
        Static-file handler that suppresses console-bound request logging.

        This avoids write failures in windowed executable builds where
        ``sys.stderr`` may be unavailable.
        """

        def log_message(self, format: str, *args) -> None:
            """
            Suppress per-request log output.

            Args:
                format (str):
                    Logging format string provided by the base handler.
                *args:
                    Positional values for the format string.

            Returns:
                None
            """
            return

    handler = partial(QuietStaticHandler, directory=str(root))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"[*] HTTP server starting on http://0.0.0.0:{port}/")
    httpd.serve_forever()

def _run_mode_from_cli(args: argparse.Namespace) -> bool:
    """
    Dispatch alternate launcher modes.

    Args:
        args (argparse.Namespace):
            Parsed launcher arguments.

    Returns:
        bool:
            True if an alternate mode was executed and normal GUI startup
            should be skipped, False otherwise.
    """
    ensure_runtime_cwd()

    if args.http_server:
        root = Path(args.root).resolve() if args.root else _project_root()
        _run_static_http_server(root, port=args.port or 8080)
        return True

    if args.ws_server:
        from server.websocket_server import main as websocket_main

        websocket_main(port=args.port or 8765)
        return True

    if args.controller:
        from controller.slide_controller import main as controller_main

        controller_main()
        return True

    if args.interruptor:
        print("[INFO] Legacy verse_output.txt interruptor mode is disabled.")
        return True

    return False

def main() -> None:
    """
    Launch the default Slide Generator application workflow.

    Returns:
        None
    """
    args = _parse_mode_args()
    if _run_mode_from_cli(args):
        return

    root = ensure_runtime_cwd()
    set_windows_app_user_model_id("org.euljirochurch.EuljiroWorship")

    # Adjust this if your overlay/static files live under a specific directory.
    # For example: http_cwd = root / "web"
    http_cwd = root

    http_p = None
    ws_p = None

    try:
        http_p = _start_http_server(http_cwd, port=8080)
        _ensure_alive(http_p, "http.server")

        ws_p = _start_ws_server(root)
        _ensure_alive(ws_p, "websocket_server")
    except Exception:
        _terminate_process(http_p)
        _terminate_process(ws_p)
        raise

    server_processes = {
        "http": http_p,
        "ws": ws_p,
    }

    # Ensure background servers are terminated when the application exits
    atexit.register(lambda: _terminate_process(server_processes["http"]))
    atexit.register(lambda: _terminate_process(server_processes["ws"]))

    # Create the Qt application object
    from PySide6.QtWidgets import QApplication
    from core.generator.settings_generator import get_font_from_settings
    from core.generator.ui.slide_generator import SlideGenerator

    app = QApplication(sys.argv)
    if Path(paths.ICON_FILE).exists():
        app.setWindowIcon(QIcon(paths.ICON_FILE))

    # Apply a consistent style across platforms
    app.setStyle("Fusion")

    # Apply user-configured font settings globally
    app.setFont(get_font_from_settings())

    def maintain_background_servers() -> None:
        """
        Keep the embedded HTTP and WebSocket helper servers alive.

        Returns:
            None
        """
        server_processes["http"] = _restart_process_if_needed(
            server_processes["http"],
            "http.server",
            lambda: _start_http_server(http_cwd, port=8080),
        )
        server_processes["ws"] = _restart_process_if_needed(
            server_processes["ws"],
            "websocket_server",
            lambda: _start_ws_server(root),
        )

    server_watchdog = QTimer(app)
    server_watchdog.setInterval(2000)
    server_watchdog.timeout.connect(maintain_background_servers)
    server_watchdog.start()

    # Also terminate servers on normal Qt shutdown
    app.aboutToQuit.connect(server_watchdog.stop)
    app.aboutToQuit.connect(lambda: _terminate_process(server_processes["http"]))
    app.aboutToQuit.connect(lambda: _terminate_process(server_processes["ws"]))

    # Instantiate and display the main Slide Generator window
    generator = SlideGenerator()
    if Path(paths.ICON_FILE).exists():
        generator.setWindowIcon(QIcon(paths.ICON_FILE))
    generator.show()

    # Enter Qt event loop and run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
