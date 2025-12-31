# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/generator/ui/contents/verse_content.py

UI content widget for editing 'verse' style slides.

This module defines `VerseContent`, a QWidget that provides an interface
for entering Bible references, fetching the corresponding verses from
the internal Bible data engine, and previewing the formatted output.

The widget supports:
- Selecting a Bible version
- Parsing and validating Scripture references
- Expanding verse ranges and full chapters
- Writing fetched verses to `verse_output.txt` for emergency overlay use

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import os
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QLineEdit, QComboBox, QTextEdit
)

from core.config import paths
from core.generator.settings_generator import get_font_from_settings
from core.generator.utils.slide_input_submitter import SlideInputSubmitter
from core.utils.bible_data_loader import BibleDataLoader
from core.utils.bible_parser import parse_reference

class VerseContent(QWidget):
    """
    Content editor widget for 'verse' (Bible verse) slides.

    This widget allows the user to input a Bible reference
    (e.g., "요한복음 3:16"), fetch the corresponding verse text from
    the selected Bible version, and preview the formatted output.

    The fetched verses are also written to `verse_output.txt` to support
    emergency subtitle overlays.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the verse slide editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator main window, used for submission
                and synchronization.
            caption (str):
                Initial Bible reference string.
            headline (str):
                Initial verse text content.

        Returns:
            None
        """
        super().__init__(parent)
        self.caption = caption
        self.headline = headline
        self.generator_window = generator_window
        with open(paths.ALIASES_VERSION_FILE, encoding="utf-8") as f:
            self.VERSION_ALIASES = json.load(f)        
        self.build_ui()

    def build_ui(self):
        """
        Construct the UI layout for verse editing.

        The layout includes:
        - A Bible version selector
        - A reference input field
        - A multi-line text preview for verse content

        The reference input is connected to dynamic verse fetching when
        the user presses Enter.
        """
        layout = QVBoxLayout(self)

        self.version_label = QLabel("성경 버전")
        self.version_dropdown = QComboBox()
        self.versions = sorted([
            fname.replace(".json", "")
            for fname in os.listdir(paths.BIBLE_DATA_DIR)
            if fname.endswith(".json")
        ])
        DEFAULT_VERSION = "대한민국 개역개정 (1998)"
        self.version_dropdown.addItems(self.versions)
        self.version_dropdown.setCurrentText(DEFAULT_VERSION if DEFAULT_VERSION in self.versions else self.versions[0])

        self.caption_label = QLabel("제목 (예: 요한복음 3:16)")
        self.caption_edit = QLineEdit(self.caption)

        self.headline_label = QLabel("본문")
        self.headline_edit = QTextEdit()
        self.headline_edit.setFont(get_font_from_settings())
        self.headline_edit.setPlainText(self.headline)

        self.caption_edit.returnPressed.connect(self.try_fetch_verse_output)

        layout.addWidget(self.version_label)
        layout.addWidget(self.version_dropdown)
        layout.addWidget(self.caption_label)
        layout.addWidget(self.caption_edit)
        layout.addWidget(self.headline_label)
        layout.addWidget(self.headline_edit)
        self.setLayout(layout)

        inputs = {
            "body": self.headline_edit,
        }
        self.submitter = SlideInputSubmitter(
            inputs,
            self.generator_window,
            self.build_verse_slide,
            ignore_widgets=[self.caption_edit],
        )

    def try_fetch_verse_output(self):
        """
        Fetch and display Bible verses based on the entered reference.

        This method:
        - Parses the reference string
        - Loads the selected Bible version
        - Expands verse ranges or full chapters if needed
        - Formats and displays the verse text
        - Writes the output to `verse_output.txt`

        Displays an error message in the preview area if parsing or loading fails.
        """
        ref = self.caption_edit.text().strip()
        version = self.version_dropdown.currentText()
        alias = self.VERSION_ALIASES.get(version, version)
        try:
            parsed = parse_reference(ref)
            if not parsed:
                self.headline_edit.setPlainText("⚠️ 유효하지 않은 성경 구절")
                return

            book_id, chapter, verses = parsed
            loader = BibleDataLoader()
            loader.load_version(version)

            if isinstance(verses, tuple) and verses[1] == -1:
                try:
                    max_verse = len(loader.get_verses(version)[book_id][str(chapter)])
                    verses = list(range(1, max_verse + 1))
                except Exception as e:
                    print(f"[ERROR] Failed to expand full chapter: {e}")
                    return
            elif isinstance(verses, tuple):
                start, end = verses
                verses = list(range(start, end + 1))

            book_alias = loader.get_standard_book(book_id, "ko")
            slides = []
            for v in verses:
                text = loader.get_verse(version, book_id, chapter, v)
                if text:
                    reftext = f"{book_alias} {chapter}장 {v}절 ({alias})"
                    slides.append({
                        "style": "verse",
                        "caption": reftext,
                        "headline": text.strip()
                    })

            full_text = "\n\n".join(f"{s['caption']}\n{s['headline']}" for s in slides)
            self.headline_edit.setPlainText(full_text)

            with open(paths.VERSE_FILE, "w", encoding="utf-8") as f:
                f.write(full_text)

            self.generated_slides = slides
            print("✅ verse_output.txt updated and slides generated")

        except Exception as e:
            self.headline_edit.setPlainText(f"❌ 구절 처리 오류: {e}")

    def build_verse_slide(self):
        """
        Conditionally build verse slide data.

        Returns slide data only if either the reference or verse text
        is non-empty.

        Returns:
            dict | None:
                Slide data dictionary if valid; otherwise, None.
        """
        data = self.get_slide_data()
        if not data["caption"] and not data["headline"]:
            return None
        return data

    def get_slide_data(self) -> dict:
        """
        Return the current verse slide data.

        Returns:
            dict:
                Dictionary containing:
                - style: 'verse'
                - caption: Bible reference string
                - headline: Verse text content
        """
        return {
            "style": "verse",
            "caption": self.caption_edit.text().strip(),
            "headline": self.headline_edit.toPlainText().strip()
        }