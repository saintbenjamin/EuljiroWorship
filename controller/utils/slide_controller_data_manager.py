# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/controller/utils/slide_controller_data_manager.py

Persistent data manager for the slide controller.

This module manages the persistent state used by the slide controller:
- Loading slide data from the active slide JSON file
- Tracking the current slide index
- Backing up slide data before emergency interruption
- Restoring slides after emergency mode is cleared

It intentionally contains no UI logic and serves as a thin I/O and state
coordination layer for SlideController.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import json
import os
import shutil

from core.config import paths

class SlideControllerDataManager:
    """
    Manages persistent slide data and controller state.

    This class is responsible for:
    - Loading slide data from disk
    - Keeping track of the current slide index
    - Backing up slide data before emergency interruption
    - Restoring slide data after emergency mode exits

    Attributes:
        slide_file (str):
            Path to the active slide JSON file.
        slides (list[dict]):
            List of currently loaded slide dictionaries.
        index (int):
            Current slide index.
        last_slide_index (int | None):
            Previously active slide index, if tracked.
    """

    def __init__(self, slide_file):
        """
        Initialize the data manager with a slide file path.

        Args:
            slide_file (str):
                Path to the JSON file currently used by the slide controller.

        Returns:
            None
        """
        self.slide_file = slide_file
        self.slides = []
        self.index = 0
        self.last_slide_index = None

    def load_slides(self):
        """
        Load slides from the active slide file into memory.

        On success, populates `self.slides` with parsed slide dictionaries.
        On failure, resets the slide list to an empty list and prints an error.

        Returns:
            None
        """
        try:
            with open(self.slide_file, "r", encoding="utf-8") as f:
                self.slides = json.load(f)
            print(f"[✓] Loaded {len(self.slides)} slides.")
        except Exception as e:
            print("[!] Failed to load slides:", e)
            self.slides = []

    def backup_slides(self):
        """
        Create a backup copy of the active slide file.

        Copies `paths.SLIDE_FILE` to `paths.SLIDE_BACKUP_FILE`.
        This backup is used to restore slides after emergency caption mode.

        Returns:
            None
        """
        try:
            shutil.copy(paths.SLIDE_FILE, paths.SLIDE_BACKUP_FILE)
        except Exception as e:
            print("[!] Slide backup failed:", e)

    def restore_from_backup(self):
        """
        Restore slide data from the backup file if available.

        Loads slides from `paths.SLIDE_BACKUP_FILE` into memory.

        Returns:
            bool:
                True if backup restoration succeeded.
                False if no backup exists or restoration failed.
        """
        restored = False

        if os.path.exists(paths.SLIDE_BACKUP_FILE):
            try:
                with open(paths.SLIDE_BACKUP_FILE, "r", encoding="utf-8") as f:
                    self.slides = json.load(f)
                print("[✓] Slide backup restored.")
                restored = True
            except Exception as e:
                print("[!] Failed to restore slides:", e)
                self.slides = []

        return restored

    def clear_backups(self):
        """
        Remove the slide backup file if it exists.

        Deletes `paths.SLIDE_BACKUP_FILE` from disk to clear stale backup state.

        Returns:
            None
        """
        if os.path.exists(paths.SLIDE_BACKUP_FILE):
            os.remove(paths.SLIDE_BACKUP_FILE)