# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/generator/ui/contents/hymn_content.py

UI content widget for editing 'hymn' style slides.

This module defines `HymnContent`, a QWidget that provides an interface for
editing hymn-based slides. It supports selecting a hymn by number, loading
its title and lyrics from local JSON files, editing the content, and saving
updates back to the hymn database.

Hymn data is stored as JSON files under a predefined directory (e.g.,
`data/hymns/`), and this widget serves as a lightweight editor and viewer
for that dataset within the slide generator.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import os
import json
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton,
    QMessageBox, QHBoxLayout, QSizePolicy
)

from core.generator.settings_generator import get_font_from_settings
from core.generator.utils.icon_helpers import set_svg_icon, get_icon_path
from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class HymnContent(QWidget):
    """
    Content editor widget for 'hymn' style slides.

    This widget provides input fields and controls for:
    - Selecting a hymn by number
    - Viewing and editing the hymn title
    - Viewing and editing the hymn lyrics
    - Loading hymn data from a local JSON database
    - Saving edited hymn data back to the database

    The edited content can be exported as slide data for use in the
    slide generator and controller.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the hymn content editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator window, used for submitting slide data
                and enabling auto-save behavior.
            caption (str):
                Initial title or caption value, often containing the hymn title.
            headline (str):
                Initial lyrics text.

        Returns:
            None
        """
        super().__init__(parent)
        self.caption = caption
        self.headline = headline
        self.hymn_data = {}
        self.generator_window = generator_window
        self.build_ui()

    def build_ui(self):
        """
        Construct the UI layout and bind widget actions.

        This method initializes all input fields and buttons, sets up layout
        structure, and attempts to automatically extract the hymn number from
        the initial caption if present.

        Args:
            None

        Returns:
            None
        """
        layout = QVBoxLayout(self)

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Enter")
        self.number_input.setFixedWidth(120)
        self.number_input.returnPressed.connect(self.load_hymn_by_number)

        self.title_edit = QLineEdit(self.caption)
        self.headline_edit = QTextEdit()
        self.headline_edit.setFont(get_font_from_settings())
        self.headline_edit.setPlainText(self.headline)

        self.load_button = QPushButton()
        set_svg_icon(self.load_button, get_icon_path("search.svg"), size=30)
        self.load_button.clicked.connect(self.load_hymn_by_number)
        self.load_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.save_button = QPushButton()
        set_svg_icon(self.save_button, get_icon_path("database-edit.svg"), size=30)
        self.save_button.clicked.connect(self.save_hymn_json)

        number_layout = QHBoxLayout()
        number_layout.addWidget(QLabel("새찬송가"))
        number_layout.addWidget(self.number_input)
        number_layout.addWidget(QLabel("장"))
        number_layout.addWidget(self.load_button)

        layout.addLayout(number_layout)
        layout.addWidget(QLabel("제목"))
        layout.addWidget(self.title_edit)
        layout.addWidget(QLabel("가사"))
        layout.addWidget(self.headline_edit)
        layout.addWidget(self.save_button)

        # Automatically extract hymn number
        match = re.search(r"새찬송가\s*(\d+)\s*장", self.caption.strip())
        if match:
            self.number_input.setText(match.group(1))

    def load_hymn_by_number(self):
        """
        Load hymn data from the local JSON database using the selected number.

        The method validates the hymn number, checks that it falls within the
        available range, and attempts to load the corresponding JSON file.
        On success, the title and lyrics fields are populated.

        Args:
            None

        Returns:
            None

        Raises:
            OSError:
                If the hymn directory cannot be accessed.
            json.JSONDecodeError:
                If the hymn JSON file exists but contains invalid data.
        """
        hymn_num = self.number_input.text().strip()
        if not hymn_num.isdigit():
            QMessageBox.warning(self, "입력 오류", "숫자만 입력하세요.")
            return

        min_num, max_num = self.get_hymn_number_range()
        int_num = int(hymn_num)
        if int_num < min_num or int_num > max_num:
            QMessageBox.warning(self, "범위 오류", f"새찬송가는 {min_num}번부터 {max_num}번까지 있습니다.")
            return

        filename = f"hymn_{int(hymn_num):03d}.json"
        path = os.path.join("data", "hymns", filename)

        try:
            with open(path, encoding="utf-8") as f:
                self.hymn_data = json.load(f)
                self.title_edit.setText(self.hymn_data.get("title", ""))
                self.headline_edit.setPlainText(self.hymn_data.get("headline", ""))
        except Exception:
            QMessageBox.warning(self, "불러오기 실패", f"파일을 읽을 수 없습니다:\n{path}")

        inputs = {
            "title": self.title_edit,
            "body": self.headline_edit,
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_hymn_slide)

    def build_hymn_slide(self):
        """
        Conditionally generate hymn slide data.

        If both the title and lyrics fields are empty, no slide data is
        generated. Otherwise, the current input values are returned as
        a slide data dictionary.

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

    def get_hymn_number_range(self):
        """
        Determine the valid range of hymn numbers from the local database.

        This method scans the hymn JSON directory and extracts the minimum
        and maximum hymn numbers available.

        Args:
            None

        Returns:
            tuple[int, int]:
                A tuple containing the minimum and maximum hymn numbers.
                Returns (0, 0) if no valid hymn files are found.
        """
        files = os.listdir("data/hymns")
        nums = [
            int(f.replace("hymn_", "").replace(".json", ""))
            for f in files if f.startswith("hymn_") and f.endswith(".json")
        ]
        return (min(nums), max(nums)) if nums else (0, 0)

    def get_slide_data(self) -> dict:
        """
        Generate the slide data dictionary for a hymn slide.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the hymn slide, including:
                - style
                - caption (hymn title)
                - headline (lyrics)
        """
        return {
            "style": "hymn",
            "caption": self.title_edit.text().strip(),
            "headline": self.headline_edit.toPlainText().strip()
        }

    def save_hymn_json(self):
        """
        Save the current hymn data back to its JSON file.

        This method updates the title and lyrics fields in the corresponding
        hymn JSON file. If the hymn number is missing or invalid, the save
        operation is aborted and the user is warned.

        Args:
            None

        Returns:
            None

        Raises:
            OSError:
                If the hymn file cannot be written.
        """
        hymn_num = self.number_input.text().strip()
        if not hymn_num.isdigit():
            QMessageBox.warning(self, "저장 오류", "먼저 번호를 입력하고 데이터를 불러오세요.")
            return

        path = os.path.join("data", "hymns", f"hymn_{int(hymn_num):03d}.json")
        self.hymn_data["title"] = self.title_edit.text()
        self.hymn_data["headline"] = self.headline_edit.toPlainText()

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.hymn_data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "저장 완료", f"새찬송가 {hymn_num}번의 데이터베이스를 업데이트하였습니다.")
        except Exception:
            QMessageBox.critical(self, "저장 실패", f"파일을 저장할 수 없습니다:\n{path}")