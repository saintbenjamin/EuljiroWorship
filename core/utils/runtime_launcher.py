# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/utils/runtime_launcher.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Runtime helpers for source and frozen executable launches.

This module centralizes small helpers used when the application needs to:

- detect whether it is running from source or from a frozen executable
- resolve the runtime application root directory
- relaunch the main entry point in alternate modes (controller/server/helper)
- normalize the current working directory for relative resource paths
"""

import os
import sys
from pathlib import Path

def is_frozen() -> bool:
    """
    Return whether the current process is running as a frozen executable.

    Returns:
        bool:
            True if the process is running from a frozen bundle
            (for example, a `PyInstaller <https://pyinstaller.org/>`_ build),
            False otherwise.
    """
    return bool(getattr(sys, "frozen", False))

def get_runtime_base_dir() -> Path:
    """
    Resolve the user-facing application root directory.

    Returns:
        pathlib.Path:
            Runtime root directory.

            - In source execution, this is the repository root.
            - In frozen execution, this is the directory containing the
              executable file.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]

def get_entry_script_path() -> Path:
    """
    Return the source entry script path for non-frozen relaunches.

    Returns:
        pathlib.Path:
            Absolute path to ``EuljiroWorship.py`` under the project root.
    """
    return get_runtime_base_dir() / "EuljiroWorship.py"

def build_entry_command(*args: str) -> list[str]:
    """
    Build a subprocess command that relaunches the main application entry point.

    This helper keeps subprocess launch behavior consistent between:

    - source execution (``python EuljiroWorship.py ...``)
    - frozen execution (``EuljiroWorship.exe ...``)

    Args:
        *args (str):
            Additional command-line arguments passed to the relaunched process.

    Returns:
        list[str]:
            Command list suitable for :class:`subprocess.Popen`.
    """
    if is_frozen():
        return [sys.executable, *args]

    return [sys.executable, str(get_entry_script_path()), *args]

def ensure_runtime_cwd() -> Path:
    """
    Change the current working directory to the runtime application root.

    This is useful for code paths that still rely on relative resource
    directories such as ``./html`` or ``./assets``.

    Returns:
        pathlib.Path:
            The runtime application root directory now used as CWD.
    """
    root = get_runtime_base_dir()
    os.chdir(root)
    return root

def set_windows_app_user_model_id(app_id: str) -> None:
    """
    Set the Windows AppUserModelID for the current process when available.

    This helps Windows display the intended application identity and icon in
    the taskbar for GUI processes, especially when launching from Python or
    from a frozen executable that spawns alternate modes.

    Args:
        app_id (str):
            Stable Windows application identifier for the current process.

    Returns:
        None
    """
    if os.name != "nt":
        return

    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass
