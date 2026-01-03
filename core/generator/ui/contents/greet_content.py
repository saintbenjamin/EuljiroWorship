# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/contents/greet_content.py

UI content widget for editing 'greet' style slides.

This module defines `GreetContent`, a QWidget that provides input fields
for greeting or message-style slides. These slides are typically used for
welcome messages, sermon titles with extended descriptions, or other
freeform announcements.

The widget supports a short caption and a multiline headline, and integrates
with `SlideInputSubmitter` to enable automatic submission and synchronization
with the parent generator window.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPlainTextEdit
from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class GreetContent(QWidget):
    """
    Content editor widget for 'greet' style slides.

    This widget provides input fields for:
    - Caption: A short reference or subtitle (e.g., Bible reference)
    - Headline: A multiline main message or greeting text

    The collected input is converted into a slide data dictionary
    containing `style`, `caption`, and `headline` fields.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the greet slide content editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator window, used for submitting slide data
                and enabling auto-save behavior.
            caption (str):
                Initial caption value (e.g., reference or short label).
            headline (str):
                Initial headline value (e.g., greeting or main message).

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
        Construct the UI elements for editing a greet-style slide.

        This method creates labeled input fields for caption and multiline
        headline content, arranges them vertically, and registers the inputs
        with `SlideInputSubmitter` to enable automatic submission.

        Args:
            None

        Returns:
            None
        """
        layout = QVBoxLayout(self)

        # Caption (subheading)
        self.caption_label = QLabel("소제 입력 (예: 사도행전 9:31)")
        self.caption_edit = QLineEdit(self.caption)

        # Headline (main message)
        self.headline_label = QLabel("본문 입력 (예: 성령의 능력으로 부흥하는 교회)")
        self.headline_edit = QPlainTextEdit(self.headline)

        # Assemble layout
        layout.addWidget(self.caption_label)
        layout.addWidget(self.caption_edit)
        layout.addWidget(self.headline_label)
        layout.addWidget(self.headline_edit)

        self.setLayout(layout)

        # Register input fields for export
        inputs = {
            "title": self.caption_edit,
            "body": self.headline_edit
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_greet_slide)

    def build_greet_slide(self):
        """
        Conditionally generate greet slide data.

        If both caption and headline fields are empty, no slide data is
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
        Generate the slide data dictionary for a greet slide.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the greet slide, including:
                - style
                - caption
                - headline
        """
        return {
            "style": "greet",
            "caption": self.caption_edit.text().strip(),
            "headline": self.headline_edit.toPlainText().strip()
        }