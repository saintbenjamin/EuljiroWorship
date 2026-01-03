# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/config/paths.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Defines core directory and file paths used across the EuljiroWorship
and EuljiroBible systems.

This module centralizes all filesystem paths required by the project,
including:

- Base project directories (root, store, settings, assets)
- Generator and controller output files
- Emergency verse output path for overlay systems
- Bible data directories and alias/config JSON files
- Shared paths used by both GUI and CLI components

All paths are resolved relative to the project root to ensure
consistent behavior across platforms (Windows, macOS, Linux).
"""

import os

# ───── Base directories ─────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # Project root
STORE_DIR = os.path.join(BASE_DIR, "store")  # Output and backup directory
SETTING_DIR = os.path.join(BASE_DIR, "json")  # JSON config and settings
ICON_DIR = os.path.join(BASE_DIR, "assets", "svg")  # SVG icon assets

# ───── Emergency overlay file ─────
VERSE_FILE = os.path.join(BASE_DIR, "verse_output.txt")  # Used by overlay system
# [FIXME] Should allow configurable path assignment in the future

# ───── Settings files ─────
SETTING_FILE = os.path.join(SETTING_DIR, "settings.json")  # General application settings
SETTING_LAST_OPEN_FILE = os.path.join(SETTING_DIR, "settings_last_path.json")  # Last opened file path

# ───── Slide system output and backup ─────
SLIDE_FILE = os.path.join(STORE_DIR, "slide_output.json")  # Main slide output
SLIDE_BACKUP_FILE = os.path.join(STORE_DIR, "slide_output_backup.json")  # Used for restoration after emergency

# ───── Bible data paths (EuljiroBible) ─────
BIBLE_DATA_DIR = os.path.join(BASE_DIR, "data")  # Full Bible version JSON files
JSON_DIR = os.path.join(BASE_DIR, "json")  # Version alias/config JSONs
BIBLE_NAME_DIR = os.path.join(JSON_DIR, "bible")  # Name alias subdirectory

# ───── Bible alias/config files ─────
ALIASES_VERSION_FILE = os.path.join(BIBLE_NAME_DIR, "aliases_version.json")  # GUI version aliases
ALIASES_VERSION_CLI_FILE = os.path.join(BIBLE_NAME_DIR, "aliases_version_cli.json")  # CLI version aliases
ALIASES_BOOK_FILE = os.path.join(BIBLE_NAME_DIR, "aliases_book.json")  # Book name aliases
STANDARD_BOOK_FILE = os.path.join(BIBLE_NAME_DIR, "standard_book.json")  # Canonical book list
SORT_ORDER_FILE = os.path.join(BIBLE_NAME_DIR, "your_sort_order.json")  # Custom book sort order