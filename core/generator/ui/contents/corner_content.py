# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/contents/corner_content.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

UI content widget for editing 'corner' style slides.

This module defines `CornerContent`, a QWidget that provides simple text
inputs for creating corner-style slides. A corner slide typically displays
a short headline and a caption in a fixed corner position on the screen,
and is commonly used for sermon titles, worship order sections, or brief
section headers.

The widget integrates with `SlideInputSubmitter` to support automatic
submission and synchronization with the parent generator window.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class CornerContent(QWidget):
    """
    Content editor widget for 'corner' style slides.

    This widget provides input fields for:
    - Headline text (main title)
    - Caption text (subtitle or secondary label)

    The collected input is converted into a slide data dictionary
    containing `style`, `caption`, and `headline` fields.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the corner slide content editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator window, used for submitting slide data
                and enabling auto-save behavior.
            caption (str):
                Initial caption text (e.g., subtitle or section label).
            headline (str):
                Initial headline text (e.g., main title).

        Returns:
            None
        """
        super().__init__(parent)
        self.caption = caption
        self.headline = headline
        self.generator_window = generator_window
        self.build_ui()

    def build_ui(self):
        """
        Construct the UI elements for editing a corner-style slide.

        This method creates labeled input fields for headline and caption,
        arranges them vertically, and registers the inputs with
        `SlideInputSubmitter` to enable automatic submission.

        Args:
            None

        Returns:
            None
        """
        layout = QVBoxLayout(self)

        # Headline input
        self.headline_label = QLabel("제목")
        self.headline_edit = QLineEdit(self.headline)

        # Caption input
        self.caption_label = QLabel("부제")
        self.caption_edit = QLineEdit(self.caption)

        # Layout widgets
        layout.addWidget(self.headline_label)
        layout.addWidget(self.headline_edit)
        layout.addWidget(self.caption_label)
        layout.addWidget(self.caption_edit)
        layout.addStretch()

        self.setLayout(layout)

        # Auto-save support
        inputs = {
            "title": self.caption_edit,
            "body": self.headline_edit
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_corner_slide)

    def build_corner_slide(self):
        """
        Conditionally generate corner slide data.

        If both the headline and caption fields are empty, no slide data is
        generated. Otherwise, the current input values are returned as a
        slide data dictionary.

        Args:
            None

        Returns:
            dict | None:
                Slide data dictionary if at least one field is non-empty;
                otherwise, None.
        """
        data = self.get_slide_data()
        if not data["caption"] and not data["headline"]:
            return None
        return data

    def get_slide_data(self) -> dict:
        """
        Generate the slide data dictionary for a corner slide.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the corner slide, including:
                - style
                - caption
                - headline
        """
        return {
            "style": "corner",
            "caption": self.caption_edit.text().strip(),
            "headline": self.headline_edit.text().strip()
        }