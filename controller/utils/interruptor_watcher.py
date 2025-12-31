# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/controller/utils/interruptor_watcher.py

Watches `verse_output.txt` and emits a Qt signal when the emergency text is cleared.

This module defines a lightweight polling watcher used by the slide controller.
It monitors the emergency verse file (`paths.VERSE_FILE`) and detects the state
transition from **non-empty** to **empty**. When that transition occurs, it emits
`InterruptorWatcher.interruptor_cleared`, allowing the controller to restore the
previous slide session and exit emergency mode.

Key behavior:
- Polls the verse file at a configurable interval (`poll_interval`)
- Emits a signal only on the transition: non-empty → empty
- Provides a stop mechanism for clean thread shutdown

Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
Telephone: +82-2-2266-3070
E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
Copyright (c) 2025 The Eulji-ro Presbyterian Church.
License: MIT License with Attribution Requirement (see LICENSE file for details)
"""

import os
import time

from PySide6.QtCore import QObject, Signal

from controller.utils.slide_controller_data_manager import SlideControllerDataManager
from core.config import paths

class InterruptorWatcher(QObject):
    """
    Monitors the emergency verse output file and emits a signal when it is cleared.

    This watcher is designed to run inside a `QThread` loop (polling-based).
    It reads `paths.VERSE_FILE` periodically and tracks the last observed content.
    When the file transitions from non-empty content to an empty string, it emits
    `interruptor_cleared`.

    Attributes:
        interruptor_cleared (Signal):
            Emitted when the verse file becomes empty after previously containing text.
    """

    interruptor_cleared = Signal()

    def __init__(self, poll_interval=1):
        """
        Initialize the watcher.

        Args:
            poll_interval (int | float):
                Time in seconds between file polls.

        Returns:
            None
        """
        super().__init__()
        self.verse_file = paths.VERSE_FILE
        self.poll_interval = poll_interval
        self._running = True
        self._last_content = None

    def stop(self):
        """
        Stop the watcher loop.

        This method signals the polling loop in `run()` to exit cleanly.
        It is intended to be called during controller shutdown.

        Args:
            None

        Returns:
            None
        """
        self._running = False

    def run(self):
        """
        Start monitoring the verse output file.

        This method runs a polling loop while `_running` is True:
        - If the verse file exists, read and strip its content.
        - If the content transitions from non-empty to empty, emit `interruptor_cleared`.
        - Sleep for `poll_interval` seconds between polls.

        Notes:
            - This is a polling-based watcher (not filesystem event-based).
            - Intended to be executed in a background `QThread`.

        Args:
            None

        Returns:
            None
        """
        while self._running:
            try:
                if os.path.exists(self.verse_file):
                    with open(self.verse_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()

                    # Detect transition from non-empty to empty
                    if content == "" and self._last_content not in (None, ""):
                        print("[✓] Detected interruptor cleared.")
                        self.interruptor_cleared.emit()

                    self._last_content = content

                time.sleep(self.poll_interval)

            except Exception as e:
                print("[!] InterruptorWatcher error:", e)

    def restore_last_slide(self):
        """
        Restore the previous slide state after emergency caption is cleared.

        This is a thin helper that delegates restoration to `SlideControllerDataManager`.
        It is not used directly by the watcher loop unless called externally.

        Args:
            None

        Returns:
            None
        """
        slide_manager = SlideControllerDataManager(paths.SLIDE_FILE)
        slide_manager.restore_last_slide()