# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/controller/utils/emergency_caption_handler.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Handles the emergency caption workflow triggered from the slide controller.

This module coordinates the emergency caption process by:

- Launching the emergency caption dialog
- Collecting finalized slide data from the dialog
- Writing emergency slides to the slide output JSON file

The handler acts as a thin orchestration layer between the UI dialog
(:class:`controller.ui.emergency_caption_dialog.EmergencyCaptionDialog`), the slide factory, and the slide output file.
"""

import json

from controller.ui.emergency_caption_dialog import EmergencyCaptionDialog
from controller.utils.emergency_slide_factory import EmergencySlideFactory
from core.config import paths

class EmergencyCaptionHandler:
    """
    Manages the emergency caption input and export workflow.

    This class is responsible for:

    - Opening the emergency caption dialog as a modal window
    - Retrieving finalized slide data from the dialog
    - Writing emergency slides to the slide output JSON file

    The handler does not perform slide parsing itself; it delegates
    slide creation to :class:`controller.ui.emergency_caption_dialog.EmergencyCaptionDialog` and :class:`controller.utils.emergency_slide_factory.EmergencySlideFactory`.
    """

    def __init__(self, parent):
        """
        Initialize the emergency caption handler.

        Args:
            parent (QWidget):
                Parent widget used to anchor the emergency caption dialog
                as a modal window.

        Returns:
            None
        """
        self.parent = parent
        self.slide_factory = EmergencySlideFactory()

    def handle(self):
        """
        Launch the emergency caption dialog and export generated slides.

        This method:
        
        - Opens the emergency caption dialog
        - Waits for user confirmation or cancellation
        - Retrieves finalized slide data from the dialog
        - Writes the slides to the configured slide output file

        If the dialog is cancelled, no file is written.

        Returns:
            list[dict] | None:
                List of generated emergency slide dictionaries if confirmed,
                or None if the dialog was cancelled.
        """
        # Launch emergency input dialog
        dialog = EmergencyCaptionDialog(self.parent)
        if not dialog.exec():
            return None  # User cancelled

        # Retrieve input lines
        slides = dialog.get_final_slides()

        # Write emergency slides to output file
        with open(paths.SLIDE_FILE, "w", encoding="utf-8") as f:
            json.dump(slides, f, ensure_ascii=False, indent=2)

        return slides