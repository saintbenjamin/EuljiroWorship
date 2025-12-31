# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/generator/ui/contents/prayer_content.py

UI content widget for editing 'prayer' style slides.

This module defines `PrayerContent`, a QWidget that provides input fields
for creating prayer slides. A prayer slide typically consists of a short
title (e.g., "기도") and the name of the person leading the prayer.

The widget integrates with `SlideInputSubmitter` to support automatic
submission and synchronization with the parent slide generator.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit

from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class PrayerContent(QWidget):
    """
    Content editor widget for 'prayer' style slides.

    This widget allows users to specify:
    - A short prayer title (usually "기도")
    - The name of the prayer leader

    The entered values are exported as a simple slide dictionary and
    rendered using the 'prayer' slide style.
    """

    def __init__(self, parent, generator_window, caption: str = "기도", headline: str = ""):
        """
        Initialize the prayer content editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator main window, used for slide submission
                and auto-save behavior.
            caption (str):
                Initial prayer title. Defaults to "기도".
            headline (str):
                Initial name of the prayer leader.

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
        Construct the UI elements for editing a prayer slide.

        This method creates labeled input fields for the prayer title and
        the prayer leader's name, arranges them vertically, and registers
        the inputs with `SlideInputSubmitter` to enable automatic submission.

        Args:
            None

        Returns:
            None
        """
        layout = QVBoxLayout(self)

        self.caption_label = QLabel("제목 (기본값: 기도)")
        self.caption_edit = QLineEdit(self.caption)

        self.headline_label = QLabel("기도인도자 (예: 이승철 장로)")
        self.headline_edit = QLineEdit(self.headline)

        layout.addWidget(self.caption_label)
        layout.addWidget(self.caption_edit)
        layout.addWidget(self.headline_label)
        layout.addWidget(self.headline_edit)
        layout.addStretch()

        self.setLayout(layout)

        inputs = {
            "title": self.caption_edit,
            "body": self.headline_edit,
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_prayer_slide)

    def build_prayer_slide(self):
        """
        Conditionally generate prayer slide data.

        If both the title and leader name fields are empty, no slide data is
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
        Generate the slide data dictionary for a prayer slide.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the prayer slide, including:
                - style
                - caption (prayer title)
                - headline (prayer leader name)
        """
        return {
            "style": "prayer",
            "caption": self.caption_edit.text().strip(),
            "headline": self.headline_edit.text().strip()
        }