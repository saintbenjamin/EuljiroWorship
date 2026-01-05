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

- An HTTP server (static file hosting; default: ``python -m http.server 8080``)
- A `WebSocket <https://websocket-client.readthedocs.io/en/latest/index.html>`_ server (real-time slide updates; launched via ``server/websocket_server.py``)

Typical usage::

    python EuljiroWorship.py

Note:
    - The HTTP document root is currently set to the project root directory. If your overlay/static files live under a specific subdirectory (e.g. ``web/``), update ``http_cwd`` accordingly.
    - Both servers are started as subprocesses. They are terminated on normal `Qt <https://doc.qt.io/qt-6/index.html>`_ exit and also via ``atexit`` as a fallback.
    - If the server subprocess exits immediately (e.g., port already in use), the launcher raises a ``RuntimeError``.
"""

import sys
import atexit
import subprocess
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Load font settings from persistent configuration
from core.generator.settings_generator import get_font_from_settings

# Import the main Slide Generator UI
from core.generator.ui.slide_generator import SlideGenerator

def _project_root() -> Path:
    """
    Return the project root directory.

    This function assumes that ``EuljiroWorship.py`` is located at the repository
    root (i.e., the root directory of the project).

    Returns:
        pathlib.Path:
            Absolute path to the project root directory.
    """
    return Path(__file__).resolve().parent

def _start_http_server(cwd: Path, port: int = 8080) -> subprocess.Popen:
    """
    Start a static-file HTTP server as a subprocess.

    Internally, this runs Python's built-in module::

        python -m http.server <port>

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
    cmd = [sys.executable, "-m", "http.server", str(port)]
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

    This launches::

        <project_root>/server/websocket_server.py

    Args:
        root (pathlib.Path):
            Absolute path to the project root directory.

    Raises:
        FileNotFoundError
            If ``server/websocket_server.py`` does not exist under ``root``.

    Returns:
        subprocess.Popen:
            A handle to the spawned `WebSocket <https://websocket-client.readthedocs.io/en/latest/index.html>`_ server process.

    Note:
        - The process is spawned with its working directory set to the project root.
        - ``start_new_session=True`` is used to improve shutdown reliability across platforms.
    """
    ws_path = root / "server" / "websocket_server.py"
    if not ws_path.exists():
        raise FileNotFoundError(f"WebSocket server not found: {ws_path}")

    cmd = [sys.executable, str(ws_path)]
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

if __name__ == "__main__":
    root = _project_root()

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

    # Ensure background servers are terminated when the application exits
    atexit.register(_terminate_process, http_p)
    atexit.register(_terminate_process, ws_p)

    # Create the Qt application object
    app = QApplication(sys.argv)

    # Apply a consistent style across platforms
    app.setStyle("Fusion")

    # Apply user-configured font settings globally
    app.setFont(get_font_from_settings())

    # Also terminate servers on normal Qt shutdown
    app.aboutToQuit.connect(lambda: _terminate_process(http_p))
    app.aboutToQuit.connect(lambda: _terminate_process(ws_p))

    # Instantiate and display the main Slide Generator window
    generator = SlideGenerator()
    generator.show()

    # Enter Qt event loop and run the application
    sys.exit(app.exec())