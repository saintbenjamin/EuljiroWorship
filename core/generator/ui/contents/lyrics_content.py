# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/contents/lyrics_content.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

UI content widget for editing "lyrics" style slides.

This module defines :class:`core.generator.ui.contents.lyrics_content.LyricsContent`, a `QWidget <https://doc.qt.io/qt-6/qwidget.html>`_ that provides input fields
for entering a song or praise title and its lyrics. The lyrics are entered
as multiline text and are later split into multiple slides according to
the generator's export rules (typically every two lines).

The widget integrates with :class:`core.generator.utils.slide_input_submitter.SlideInputSubmitter` to support automatic
submission and synchronization with the parent generator window.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QSizePolicy
)

from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class LyricsContent(QWidget):
    """
    Content editor widget for "lyrics" style slides.

    This widget collects:

    - Song/praise title (stored in ``caption``)
    - Multiline lyrics body (stored in ``headline`` as raw text)

    The widget intentionally stores lyrics as raw, unsplit text. The slide
    export pipeline is responsible for splitting the lyrics into multiple
    slides (e.g., two lines per slide, special split markers like "(간주)",
    etc.), so the editor remains focused on input and synchronization.

    This widget integrates with the generator window via
    :class:`core.generator.utils.slide_input_submitter.SlideInputSubmitter`
    so that edits can be submitted automatically.

    Attributes:
        caption (str):
            Initial title value passed at construction time.
        headline (str):
            Initial lyrics body passed at construction time (raw multiline text).
        generator_window:
            Reference to the generator window that receives slide updates and
            manages auto-save/session behavior.
        caption_label (QLabel):
            Label describing the title input.
        caption_edit (QLineEdit):
            Input field for the lyrics title (slide ``caption``).
        headline_label (QLabel):
            Label describing the lyrics body input.
        headline_edit (QPlainTextEdit):
            Multiline editor for raw lyrics text (slide ``headline``).
        submitter (SlideInputSubmitter):
            Auto-submit helper that observes inputs and provides updated slide
            payloads via ``build_lyrics_slide()``.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the "lyrics"-style content editor.

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
        Construct the UI elements for editing a "lyrics"-style slide.

        This method creates labeled input fields for the lyrics title and
        multiline lyrics content, arranges them vertically, and registers
        the title input with :class:`core.generator.utils.slide_input_submitter.SlideInputSubmitter` to enable automatic
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
        Conditionally generate "lyrics"-style slide data.

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
        Generate the slide data dictionary for a "lyrics"-style slide.

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