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
#: Absolute path to the project root directory.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Directory for slide output and backup files (under ``BASE_DIR/store``).
STORE_DIR = os.path.join(BASE_DIR, "store")

#: Directory for JSON configs and settings (under ``BASE_DIR/json``).
SETTING_DIR = os.path.join(BASE_DIR, "json")

#: Directory for SVG icon assets (under ``BASE_DIR/assets/svg``).
ICON_DIR = os.path.join(BASE_DIR, "assets", "svg")

# ───── Emergency overlay file ─────
#: Emergency verse output file path (typically ``BASE_DIR/verse_output.txt``).
#:
#: This file is written by the emergency caption flow and monitored by
#: helper processes such as the verse interruptor.
VERSE_FILE = os.path.join(BASE_DIR, "verse_output.txt")

# ───── Settings files ─────
#: Main application settings JSON file (typically ``json/settings.json``).
SETTING_FILE = os.path.join(SETTING_DIR, "settings.json")

#: JSON file storing the last opened path/session info
#: (typically ``json/settings_last_path.json``).
SETTING_LAST_OPEN_FILE = os.path.join(SETTING_DIR, "settings_last_path.json")

# ───── Slide system output and backup ─────
#: Main slide output JSON file written for overlay display
#: (typically ``store/slide_output.json``).
SLIDE_FILE = os.path.join(STORE_DIR, "slide_output.json")

#: Backup of the previous slide output used for restoration after
#: emergency mode (typically ``store/slide_output_backup.json``).
SLIDE_BACKUP_FILE = os.path.join(STORE_DIR, "slide_output_backup.json")

# ───── Bible data directories (EuljiroBible) ─────
#: Directory containing Bible version JSON data files (typically ``data/``).
BIBLE_DATA_DIR = os.path.join(BASE_DIR, "data")

#: Directory containing JSON configs.
#:
#: This directory is the same physical location as ``SETTING_DIR``.
JSON_DIR = os.path.join(BASE_DIR, "json")

#: Directory containing Bible name/version alias JSON files
#: (typically ``json/bible/``).
BIBLE_NAME_DIR = os.path.join(JSON_DIR, "bible")

# ───── Bible alias/config files ─────
#: GUI Bible version alias mapping JSON file.
ALIASES_VERSION_FILE = os.path.join(BIBLE_NAME_DIR, "aliases_version.json")

#: CLI Bible version alias mapping JSON file
#: (simplified aliases for CLI parsing).
ALIASES_VERSION_CLI_FILE = os.path.join(BIBLE_NAME_DIR, "aliases_version_cli.json")

#: Book name alias mapping JSON file.
ALIASES_BOOK_FILE = os.path.join(BIBLE_NAME_DIR, "aliases_book.json")

#: Canonical book list JSON file used as the standard reference.
STANDARD_BOOK_FILE = os.path.join(BIBLE_NAME_DIR, "standard_book.json")

#: Custom book sort order JSON file.
SORT_ORDER_FILE = os.path.join(BIBLE_NAME_DIR, "your_sort_order.json")