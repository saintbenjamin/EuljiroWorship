# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/utils/slide_input_submitter.py

Handles submission logic for slide input forms in the slide generator UI.

This module defines `SlideInputSubmitter`, which listens for Enter key presses
on specified input widgets and triggers slide generation. It allows Shift+Enter
to insert line breaks in multi-line fields.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

from typing import Callable
from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtWidgets import QWidget, QApplication

class SlideInputSubmitter(QObject):
    """
    Event-filter helper that submits slide edits when the user presses Enter.

    This object installs an event filter on a set of input widgets (e.g., QLineEdit,
    QTextEdit/QPlainTextEdit, custom widgets) and interprets the Enter/Return key as a
    "submit" trigger.

    Behavior rules:
    - Enter/Return triggers submission.
    - Shift+Enter is treated as a literal newline (i.e., it does *not* submit).
    - Widgets listed in `ignore_widgets` are excluded from Enter-submit handling.

    Notes
    -----
    Submission is performed by calling `build_slide_func()`. If it returns a falsy value
    (None / empty), nothing happens. If the generator exposes `save_slides_to_file`,
    the submitter will save automatically after a successful build.

    Args:
        inputs (dict[str, QWidget]): Mapping of logical input names to widget instances.
            All widgets in this mapping receive this object's event filter.
        generator (QWidget): The generator window/controller instance. If it provides
            `save_slides_to_file(show_message: bool)`, it will be called after submission.
        build_slide_func (Callable[[], dict | list | None]): Callable that constructs
            slide data (single dict or list of dicts) from current widget state.
        ignore_widgets (list[QWidget] | None): Optional list of widgets whose Enter key
            should be ignored by this submitter.
    """

    def __init__(
        self,
        inputs: dict[str, QWidget],
        generator: QWidget,
        build_slide_func: Callable[[], dict | list | None],
        ignore_widgets=None
    ):
        """
        Initialize the submitter and install event filters on input widgets.

        Args:
            inputs (dict[str, QWidget]): Widgets to monitor for Enter-submit.
            generator (QWidget): Receiver/owner that performs persistence operations.
            build_slide_func (Callable[[], dict | list | None]): Slide builder callback.
            ignore_widgets (list[QWidget] | None): Widgets to exclude from Enter-submit.
        """
        super().__init__()
        self.inputs = inputs
        self.generator = generator
        self.build_slide_func = build_slide_func
        self.ignore_widgets = ignore_widgets or []

        # Install event filters on all monitored widgets
        for widget in self.inputs.values():
            widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Intercept keypress events to detect Enter-submit.

        - If `obj` is in `ignore_widgets`, this filter does nothing.
        - If the key is Enter/Return:
            - Shift+Enter passes through (newline behavior).
            - Otherwise, submit and consume the key event.

        Args:
            obj: Event source object (typically one of the registered widgets).
            event: Incoming Qt event.

        Returns:
            bool: True if the event was handled here (consumed), else False.
        """
        if obj in self.ignore_widgets:
            return False

        if event.type() == QEvent.Type.KeyPress:
            if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                if QApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier:
                    return False  # Allow Shift+Enter for newline
                self.try_submit_slide()
                return True

        return super().eventFilter(obj, event)

    def try_submit_slide(self):
        """
        Build and persist slide data using the registered callback.

        Workflow:
        1) Call `build_slide_func()` to obtain slide data.
        2) If slide data is falsy, do nothing.
        3) If the generator provides `save_slides_to_file`, save silently.
        4) Restore focus to the first registered input widget for fast iteration.
        """
        result = self.build_slide_func()
        if not result:
            return

        if hasattr(self.generator, "save_slides_to_file"):
            self.generator.save_slides_to_file(show_message=False)

        # Return focus to first input field
        first = list(self.inputs.values())[0]
        first.setFocus()