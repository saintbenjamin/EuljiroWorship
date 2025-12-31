# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/plugin/controller_launcher.py

Launches and manages the slide controller subprocess for integrated slide output control.

This module provides a small utility class responsible for starting the
slide controller (`controller/slide_controller.py`) as a subprocess.
It ensures that the controller is launched only once and keeps track
of the running process for basic status checks.

The launcher is intended to be used by the slide generator or main
application entry point, allowing the controller to behave as a managed
child process rather than a standalone application.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import sys
import subprocess
from PySide6.QtWidgets import QMessageBox

class SlideControllerLauncher:
    """
    Manages the lifecycle of the slide controller subprocess.

    This class encapsulates the logic for launching and tracking the
    slide controller process. It prevents duplicate launches and
    provides a simple interface for checking whether the controller
    is currently running.

    The class does not attempt to restart or forcibly terminate the
    controller; it only performs minimal lifecycle supervision suitable
    for a UI-driven workflow.
    """

    def __init__(self):
        """
        Initialize the slide controller launcher.

        The launcher starts with no active subprocess. Once the slide
        controller is launched, the subprocess handle is stored internally
        and reused for subsequent status checks.

        Returns:
            None
        """
        self.proc = None  # Currently tracked controller process

    def is_running(self) -> bool:
        """
        Check whether the slide controller process is currently running.

        This method verifies that a subprocess has been launched and that
        it has not yet terminated.

        Returns:
            bool:
                True if the controller subprocess is active,
                False otherwise.
        """
        return self.proc is not None and self.proc.poll() is None

    def launch_if_needed(self, parent_widget=None):
        """
        Launch the slide controller subprocess if it is not already running.

        If the controller process is already active, this method exits
        without performing any action.

        If the launch fails, an error message is reported as follows:
        - If a Qt parent widget is provided, a warning dialog is shown.
        - Otherwise, the error is printed to standard output.

        Args:
            parent_widget (QWidget | None):
                Optional parent widget used for displaying error dialogs.

        Returns:
            None
        """
        if self.is_running():
            print("[i] Slide controller is already running")
            return

        try:
            # Attempt to launch the controller subprocess
            self.proc = subprocess.Popen([sys.executable, "controller/slide_controller.py"])
            print("[✓] Slide controller started")

        except Exception as e:
            # Display error dialog if parent is a Qt widget
            if parent_widget:
                QMessageBox.warning(
                    parent_widget,
                    "Failed to launch slide controller",
                    f"Error:\n{e}"
                )
            else:
                print(f"[!] Failed to launch slide controller: {e}")