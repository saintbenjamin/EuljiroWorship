# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/settings_last_path.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Handles local UI state related to the last opened slide file path.

This module provides a minimal persistence layer for remembering
the most recently opened slide JSON file in the generator UI.
The path is stored as a small JSON file under the generator settings directory.
"""

import json
import os

from core.config import paths

def load_last_path():
    """
    Load the most recently opened slide file path.

    This function reads the JSON file defined by
    :py:data:`core.config.paths.SETTING_LAST_OPEN_FILE` and extracts the stored
    ``"last_opened_file"`` value.

    If the settings file does not exist or the key is missing,
    the function safely returns None.

    Returns:
        str | None:
            Absolute path of the last opened slide file,
            or None if no previous path is recorded.
    """
    if os.path.exists(paths.SETTING_LAST_OPEN_FILE):
        with open(paths.SETTING_LAST_OPEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("last_opened_file")
    return None

def save_last_path(path):
    """
    Save the most recently opened slide file path.

    The given path is written to a small JSON file located at
    :py:data:`core.config.paths.SETTING_LAST_OPEN_FILE`. 
    
    The parent directory is
    created automatically if it does not already exist.

    Args:
        path (str):
            Absolute path of the slide file to persist.

    Returns:
        None
    """
    os.makedirs(os.path.dirname(paths.SETTING_LAST_OPEN_FILE), exist_ok=True)
    with open(paths.SETTING_LAST_OPEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_opened_file": path}, f, ensure_ascii=False, indent=2)