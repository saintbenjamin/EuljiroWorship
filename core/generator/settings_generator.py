# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/settings_generator.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Handles persistent generator settings for the Slide Generator/Controller.

This module provides a small persistence layer for generator UI preferences,
stored as a JSON file (:py:data:`core.config.paths.SETTING_FILE`). It currently supports:

- Font family (e.g., "Malgun Gothic")
- Font size (int)
- Font weight (string name matching `QFont.Weight`, e.g., "Normal", "Bold")
- (Optional) emergency caption output path (e.g., ``verse_output.txt`` path)

The settings are used to build a `QFont` instance for UI widgets in the generator.
"""

import os
import json

from PySide6.QtGui import QFont
from core.config import paths

# Path to the JSON file that stores generator settings
SETTINGS_FILE = paths.SETTING_FILE

def load_generator_settings():
    """
    Load generator settings from the JSON settings file.

    If the settings file does not exist, an empty dictionary is returned.

    The returned dictionary may include keys such as:

    - "font_family": str
    - "font_size": int
    - "font_weight": str (e.g., "Normal", "Bold")
    - "verse_output_path": str (optional)

    Returns:
        dict:
            Dictionary containing persisted generator settings.
            Returns an empty dict if no settings file exists.
    """
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_generator_settings(data):
    """
    Save generator settings to the JSON settings file.

    This function writes the provided settings dictionary to, :py:data:`core.config.paths.SETTING_FILE` creating parent directories if needed.

    Note:
        This function is currently unused but reserved for future
        persistence and configuration UI logic.

    Args:
        data (dict):
            Dictionary containing generator settings to persist.

    Returns:
        None
    """
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_font_from_settings(limit_ui_size=True):
    """
    Create a QFont instance based on persisted generator settings.

    The font family, size, and weight are read from the settings file.
    When ``limit_ui_size`` is enabled, the font size is clamped to a safe
    UI range to prevent layout issues.

    Args:
        limit_ui_size (bool, optional):
            Whether to clamp the font size to the range 8-14 pt.
            Defaults to ``True``.

    Returns:
        `QFont`:
            Configured `QFont` instance for use in generator UI widgets.
    """
    settings = load_generator_settings()

    # Initialize base font
    font = QFont()
    font.setFamily(settings.get("font_family", "Malgun Gothic"))

    # Clamp font size for UI stability
    size = settings.get("font_size", 12)
    if limit_ui_size:
        size = max(8, min(size, 14))
    font.setPointSize(size)

    # Apply font weight (e.g., "Normal", "Bold")
    weight_name = settings.get("font_weight", "Normal")
    weight_value = getattr(QFont.Weight, weight_name, QFont.Weight.Normal)
    font.setWeight(weight_value)

    return font