# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/contents/anthem_content.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

UI content widget for editing "anthem" style slides.

This module defines :class:`core.generator.ui.contents.anthem_content.AnthemContent`, a `QWidget <https://doc.qt.io/qt-6/qwidget.html>`_ responsible for collecting
input data required to generate an "anthem"-style slide. The widget provides
fields for specifying the choir name and the anthem title, and converts the
input into a standardized slide dictionary used by the generator.

The widget integrates with :class:`core.generator.utils.slide_input_submitter.SlideInputSubmitter` to support automatic
submission and synchronization with the parent generator window.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class AnthemContent(QWidget):
    """
    Content editor widget for "anthem" style slides.

    This widget provides input fields for composing anthem-style slides,
    typically used for choir or special music presentations. It allows
    the user to specify:

    - Choir or group name
    - Anthem title

    The collected input is transformed into a slide dictionary containing
    ``caption``, ``caption_choir``, and ``headline`` fields, which are later
    consumed by the slide generator/exporter and controller.

    Attributes:
        caption (str):
            Initial caption text passed from existing slide data.
            Typically represents the main group or choir name.
        headline (str):
            Initial headline text passed from existing slide data.
            Typically represents the anthem title.
        generator_window:
            Reference to the slide generator window. Used for automatic
            submission, synchronization, and triggering save/update logic.
        name_input (QLineEdit):
            Input field for choir or group name.
        headline_input (QLineEdit):
            Input field for the anthem title.
        submitter (SlideInputSubmitter):
            Helper object that watches input fields and submits slide data
            back to the generator window when changes occur.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the anthem content editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator window, used for submitting slide data
                and triggering auto-save behavior.
            caption (str):
                Initial caption value, typically containing the choir name.
            headline (str):
                Initial headline value, typically containing the anthem title.

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
        Construct the UI elements for editing an "anthem"-style slide.

        This method builds input fields for the choir name and anthem title,
        arranges them vertically, and registers the inputs with
        :class:`core.generator.utils.slide_input_submitter.SlideInputSubmitter` to enable automatic submission and synchronization
        with the generator window.

        Args:
            None

        Returns:
            None
        """
        layout = QVBoxLayout(self)

        # Parse caption into components
        parts = self.caption.strip().split()
        choir = parts[1] if len(parts) == 2 else ""
        name = parts[0] if len(parts) == 2 else self.caption

        # Choir name input
        self.name_label = QLabel("찬양대 이름 (예: 글로리아 합창단. 기본값은 \"찬양대\")")
        self.name_input = QLineEdit(f"{name} {choir}".strip())

        # Anthem title input
        self.headline_label = QLabel("찬양 제목")
        self.headline_input = QLineEdit(self.headline)

        # Layout
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.headline_label)
        layout.addWidget(self.headline_input)
        layout.addStretch()

        self.setLayout(layout)

        inputs = {
            "title": self.name_input,
            "body": self.headline_input
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_anthem_slide)

    def build_anthem_slide(self):
        """
        Conditionally generate anthem slide data.

        This method checks whether at least one input field contains non-empty
        text. If all inputs are empty, no slide data is generated.

        Args:
            None

        Returns:
            dict | None:
                Slide data dictionary if at least one input is provided;
                otherwise, None.
        """
        name_text = self.name_input.text().strip()
        title = self.headline_input.text().strip()

        if not name_text and not title:
            return None
        return self.get_slide_data()

    def get_slide_data(self) -> dict:
        """
        Generate the slide data dictionary for an anthem slide.

        The method parses the choir name input to separate the main caption
        and choir identifier. Default values are applied when the input does
        not match the expected format.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the anthem slide, including:

                - style
                - caption
                - caption_choir
                - headline
        """
        parts = self.name_input.text().strip().split()

        if len(parts) == 2:
            return {
                "style": "anthem",
                "caption": parts[0],
                "caption_choir": parts[1],
                "headline": self.headline_input.text().strip()
            }
        elif len(parts) == 1:
            return {
                "style": "anthem",
                "caption": parts[0],
                "caption_choir": "찬양대",
                "headline": self.headline_input.text().strip()
            }
        else:
            return {
                "style": "anthem",
                "caption": "을지로",
                "caption_choir": "찬양대",
                "headline": "제목을 입력하세요"
            }