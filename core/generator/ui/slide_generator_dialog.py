# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/slide_generator_dialog.py

Modal dialog for editing a single slide.

This module defines `SlideGeneratorDialog`, a QDialog wrapper that reuses the
existing right-hand content panel (`SlideGeneratorRightContents`) inside a
modal dialog context. It allows slide editing via the same style-specific UI
used in the main generator, but with explicit OK/Cancel semantics.

The dialog itself contains no slide-specific logic; it delegates all content
handling to the embedded right-panel widget and simply returns the edited
result when accepted.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox

from core.generator.ui.slide_generator_right_contents import SlideGeneratorRightContents

class SlideGeneratorDialog(QDialog):
    """
    Modal dialog for editing a single slide.

    This dialog embeds `SlideGeneratorRightContents` to provide the same
    style-specific editing UI used elsewhere in the generator, but presents
    it in a blocking modal dialog with explicit OK and Cancel buttons.

    The dialog is intended to be used as follows:
    - Construct with the slide style and initial caption/headline.
    - Call `exec()` to display the dialog modally.
    - If the dialog is accepted, call `get_result()` to retrieve edited data.
    """

    def __init__(self, style: str, caption: str, headline: str, parent=None):
        """
        Initialize the slide editor dialog.

        This constructor creates a modal dialog window, embeds a
        `SlideGeneratorRightContents` widget configured for the given slide style,
        and adds a standard OK/Cancel button box.

        Args:
            style (str):
                Internal slide style key (e.g., "lyrics", "verse", "anthem").
            caption (str):
                Initial caption value to pre-fill the editor.
            headline (str):
                Initial headline or main content value to pre-fill the editor.
            parent (QWidget | None):
                Optional parent widget for modal ownership.

        Returns:
            None
        """
        super().__init__(parent)
        self.setWindowTitle("슬라이드 편집")
        self.setMinimumWidth(640)

        # Use existing right-panel widget
        self.content_widget = SlideGeneratorRightContents(
            style=style,
            generator_window=self,
            caption=caption,
            headline=headline
        )

        # OK/Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.content_widget)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_result(self) -> dict:
        """
        Return the edited slide data from the dialog.

        This method should only be called after the dialog has been accepted
        (i.e., `exec()` returned `QDialog.Accepted`). The returned dictionary
        is produced by the embedded content widget and represents the fully
        edited slide data.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the edited slide content.
        """
        return self.content_widget.get_slide_data()