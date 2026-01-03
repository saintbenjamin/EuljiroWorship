# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/contents/lyrics_content.py

UI content widget for editing 'lyrics' style slides.

This module defines `LyricsContent`, a QWidget that provides input fields
for entering a song or praise title and its lyrics. The lyrics are entered
as multiline text and are later split into multiple slides according to
the generator's export rules (typically every two lines).

The widget integrates with `SlideInputSubmitter` to support automatic
submission and synchronization with the parent generator window.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QSizePolicy
)

from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class LyricsContent(QWidget):
    """
    Content editor widget for 'lyrics' style slides.

    This widget allows users to enter:
    - A title for the song or praise
    - Multiline lyrics text

    The lyrics content is stored as raw text and later processed by the
    slide exporter, which splits the text into multiple slides according
    to predefined rules (e.g., two lines per slide).
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the lyrics content editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator main window, used for submitting
                slide data and enabling auto-save behavior.
            caption (str):
                Initial title text for the lyrics slide.
            headline (str):
                Initial lyrics content.

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
        Construct the UI elements for editing a lyrics-style slide.

        This method creates labeled input fields for the lyrics title and
        multiline lyrics content, arranges them vertically, and registers
        the title input with `SlideInputSubmitter` to enable automatic
        submission.

        Args:
            None

        Returns:
            None
        """
        layout = QVBoxLayout(self)

        self.caption_label = QLabel("찬양 제목")
        self.caption_edit = QLineEdit(self.caption)

        self.headline_label = QLabel("찬양 가사 (2줄마다 슬라이드 분할)")
        self.headline_edit = QPlainTextEdit(self.headline)
        self.headline_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.caption_label)
        layout.addWidget(self.caption_edit)
        layout.addWidget(self.headline_label)
        layout.addWidget(self.headline_edit)

        self.setLayout(layout)

        inputs = {
            "title": self.caption_edit,
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_lyrics_slide)

    def build_lyrics_slide(self):
        """
        Conditionally generate lyrics slide data.

        If both the title and lyrics fields are empty, no slide data is
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
        Generate the slide data dictionary for a lyrics slide.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the lyrics slide, including:
                - style
                - caption (song title)
                - headline (raw lyrics text)
        """
        return {
            "style": "lyrics",
            "caption": self.caption_edit.text().strip(),
            "headline": self.headline_edit.toPlainText().strip()
        }