# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/utils/logger.py

Provides error and debug logging utilities for EuljiroBible.

This module defines a lightweight logging wrapper around Python's
standard `logging` module, with the following design goals:

- Logs are written to disk only when actually needed
- A single central log file is used across the application
- Debug logging is enabled conditionally via the DEBUG environment variable
- Duplicate handlers are avoided to support hot-reload scenarios

The logger is primarily intended for internal error reporting and
optional debug tracing, not for verbose application logging.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import logging
import os

from core.config import paths

# Initialize logger
logger = logging.getLogger("EuljiroLogger")

# Avoid duplicate handlers (e.g., hot reload)
if not logger.hasHandlers():
    DEBUG_MODE = os.environ.get("DEBUG") == "1"
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.ERROR)

    # FileHandler is only added if error/debug logging occurs
    _file_handler = None

    def _ensure_file_handler():
        """
        Ensure that a file handler is attached to the global logger.

        This function lazily initializes a `logging.FileHandler` and
        attaches it to the module-level logger only once.

        The log file is created only when an error or debug message
        is actually emitted, avoiding unnecessary file I/O during
        normal execution.

        Returns:
            None
        """
        global _file_handler
        if _file_handler is None:
            _file_handler = logging.FileHandler(paths.LOG_FILE, encoding="utf-8")
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            _file_handler.setFormatter(formatter)
            logger.addHandler(_file_handler)
else:
    DEBUG_MODE = logger.level == logging.DEBUG
    _file_handler = None

def log_error(e):
    """
    Log an exception as an error with full traceback information.

    This function ensures that the file handler is initialized,
    then records the exception message along with its traceback
    using ERROR log level.

    The log file is created only when this function is called.

    Args:
        e (Exception):
            The exception instance to be logged.

    Returns:
        None
    """
    _ensure_file_handler()
    logger.error(str(e), exc_info=True)


def log_debug(msg):
    """
    Log a debug message if DEBUG mode is enabled.

    Debug mode is determined by the environment variable `DEBUG=1`
    at application startup. If DEBUG mode is disabled, this
    function performs no action.

    Args:
        msg (str):
            The debug message to record.

    Returns:
        None
    """
    if DEBUG_MODE:
        _ensure_file_handler()
        logger.debug(msg)