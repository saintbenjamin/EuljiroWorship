# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/controller/utils/slide_file_watcher.py

Slide file watcher for the slide controller.

This module continuously monitors the slide output JSON file used by the
slide controller. It detects file modification events via polling and emits
Qt signals when:

- Slide content is updated (non-empty JSON)
- Slide content is cleared (empty JSON), typically indicating the end of
  emergency caption mode

The watcher is designed to run inside a QThread and communicate with the
SlideController via Qt signals only.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import json
import os
import time

from PySide6.QtCore import QObject, Signal

class SlideFileWatcher(QObject):
    """
    Watches a slide JSON file and emits signals on content changes.

    This watcher polls the target slide file at a fixed interval and detects
    changes using the file's modified timestamp.

    Signals:
        slide_changed(list, int):
            Emitted when the slide file is updated with non-empty content.
            The second argument represents the initial slide index.
        slide_cleared():
            Emitted when the slide file becomes empty, typically signaling
            the end of emergency caption mode.
    """

    slide_changed = Signal(list, int)  # slides, index
    slide_cleared = Signal()           # empty file → need for restore

    def __init__(self, slide_file, poll_interval=1):
        """
        Initialize the slide file watcher.

        Args:
            slide_file (str):
                Path to the JSON slide file to monitor.
            poll_interval (int, optional):
                Polling interval in seconds. Defaults to 1.

        Returns:
            None
        """
        super().__init__()
        self.slide_file = slide_file
        self.poll_interval = poll_interval
        self._running = True
        self._last_mtime = None

    def stop(self):
        """
        Stop the file watching loop.

        This method signals the watcher to exit its polling loop gracefully.

        Returns:
            None
        """
        self._running = False

    def run(self):
        """
        Start monitoring the slide file for changes.

        This method runs an infinite polling loop while the watcher is active.
        When a file modification is detected:

        - Emits `slide_changed` if the file contains slide data
        - Emits `slide_cleared` if the file is empty

        This method is intended to be executed inside a QThread.

        Returns:
            None
        """
        while self._running:
            try:
                if os.path.exists(self.slide_file):
                    mtime = os.path.getmtime(self.slide_file)

                    # Initialize last modified time
                    if self._last_mtime is None:
                        self._last_mtime = mtime

                    # Check for file change
                    elif mtime != self._last_mtime:
                        self._last_mtime = mtime
                        print("[✓] Detected slide file change")

                        with open(self.slide_file, "r", encoding="utf-8") as f:
                            new_slides = json.load(f)

                        # Emit appropriate signal based on file content
                        if not new_slides:
                            print("[!] Slide file cleared.")
                            self.slide_cleared.emit()
                        else:
                            self.slide_changed.emit(new_slides, 0)

                time.sleep(self.poll_interval)

            except Exception as e:
                print("[!] SlideFileWatcher error:", e)