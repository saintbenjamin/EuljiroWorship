# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/contents/respo_content.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

UI content widget for editing 'respo' (responsive reading) style slides.

This module defines `RespoContent`, a QWidget that provides a table-based
editor for responsive readings (교독문). Each slide consists of a title
and a sequence of speaker–response pairs, which are rendered as formatted
HTML for slide output.

The widget supports loading and saving responsive readings from JSON files
stored under `data/respo/`, and integrates with `SlideInputSubmitter` for
automatic synchronization with the slide generator.
"""

import os
import re
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QSizePolicy
)
from core.generator.utils.icon_helpers import set_svg_icon, get_icon_path
from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class RespoContent(QWidget):
    """
    Content editor widget for 'respo' (responsive reading) slides.

    This widget allows users to:
    - Select a responsive reading by number
    - Edit the title of the reading
    - Edit speaker–response pairs using a table interface

    The table contents are converted into formatted HTML and exported
    as slide data for rendering.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the responsive reading editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator main window, used for submission
                and auto-save behavior.
            caption (str):
                Initial slide caption, typically a numbered title.
            headline (str):
                Initial slide body content (unused for direct editing; rebuilt
                from table data).

        Returns:
            None
        """
        super().__init__(parent)
        self.caption = caption
        self.headline = headline
        self.respo_data = {}
        self.generator_window = generator_window
        self.build_ui()

    def build_ui(self):
        """
        Construct the UI layout for responsive reading editing.

        The layout includes:
        - A number input field with load button
        - A title input field
        - A two-column table for speaker and response text
        - A save button for writing data back to JSON

        This method also initializes auto-loading when a numbered caption
        is detected.
        """
        layout = QVBoxLayout(self)

        # Load by number
        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Enter")
        self.number_input.setFixedWidth(80)
        self.number_input.returnPressed.connect(self.load_respo_by_number)

        self.load_button = QPushButton()
        set_svg_icon(self.load_button, get_icon_path("search.svg"), size=30)
        self.load_button.clicked.connect(self.load_respo_by_number)
        self.load_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        number_layout = QHBoxLayout()
        number_layout.addWidget(QLabel("새교독문"))
        number_layout.addWidget(self.number_input)
        number_layout.addWidget(QLabel("번"))
        number_layout.addWidget(self.load_button)
        layout.addLayout(number_layout)

        self.capt_edit = QLineEdit(self.caption)
        layout.addWidget(QLabel("제목"))
        layout.addWidget(self.capt_edit)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["화자", "본문"])
        self.table.verticalHeader().setDefaultSectionSize(44)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(QLabel("본문"))
        layout.addWidget(self.table)

        self.save_button = QPushButton()
        set_svg_icon(self.save_button, get_icon_path("database-edit.svg"), size=30)
        self.save_button.clicked.connect(self.save_respo_json)
        layout.addWidget(self.save_button)

        match = re.match(r"^(\d{1,3})\.", self.caption.strip())
        if match:
            self.number_input.setText(match.group(1))
            self.load_respo_by_number()

        inputs = {
            "title": self.capt_edit,
            "body": self.table,
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_respo_slide)

    def load_respo_by_number(self):
        """
        Load responsive reading data from a JSON file.

        The JSON file is selected based on the number entered by the user
        and must exist under the `data/respo/` directory. The loaded data
        populates the title field and the speaker–response table.

        Displays a warning dialog if the input is invalid or out of range.
        """
        num = self.number_input.text().strip()
        if not num.isdigit():
            QMessageBox.warning(self, "입력 오류", "숫자만 입력하세요.")
            return

        filename = f"responsive_{int(num):03d}.json"
        path = os.path.join("data", "respo", filename)

        min_num, max_num = self.get_respo_number_range()
        int_num = int(num)
        if int_num < min_num or int_num > max_num:
            QMessageBox.warning(
                self,
                "범위 오류",
                f"새교독문은 {min_num}번부터 {max_num}번까지 있습니다."
            )
            return

        try:
            with open(path, encoding="utf-8") as f:
                self.respo_data = json.load(f)
                self.capt_edit.setText(self.respo_data.get("title", ""))

                slides = self.respo_data.get("slides", [])
                self.table.setRowCount(len(slides))
                for row, slide in enumerate(slides):
                    self.table.setItem(row, 0, QTableWidgetItem(slide.get("speaker", "")))
                    self.table.setItem(row, 1, QTableWidgetItem(slide.get("headline", "")))

        except Exception as e:
            QMessageBox.warning(self, "불러오기 실패", f"파일을 읽을 수 없습니다:\n{path}")

    def build_respo_slide(self):
        """
        Conditionally generate responsive reading slide data.

        If both the title and formatted body are empty, no slide data is
        produced. Otherwise, the current table contents are formatted and
        returned as slide data.

        Returns:
            dict | None:
                Slide data dictionary if valid; otherwise, None.
        """
        data = self.get_slide_data()
        if not data["caption"] and not data["headline"]:
            return None
        return data

    def get_respo_number_range(self):
        """
        Determine the valid range of responsive reading numbers.

        Scans the `data/respo/` directory for available JSON files and
        extracts their numeric identifiers.

        Returns:
            tuple[int, int]:
                Minimum and maximum available responsive reading numbers.
        """
        files = os.listdir("data/respo")
        nums = [
            int(f.replace("responsive_", "").replace(".json", ""))
            for f in files if f.startswith("responsive_") and f.endswith(".json")
        ]
        return (min(nums), max(nums)) if nums else (0, 0)

    def get_slide_data(self):
        """
        Generate the slide data dictionary for export.

        Returns:
            dict:
                Dictionary containing:
                - style: 'respo'
                - caption: title of the responsive reading
                - headline: formatted HTML body
        """
        return {
            "style": "respo",
            "caption": self.capt_edit.text().strip(),
            "headline": self.format_responsive_text()
        }

    def format_responsive_text(self):
        """
        Convert table contents into formatted HTML text.

        Each row in the table is rendered as a bold speaker label followed
        by the corresponding response text.

        Returns:
            str:
                HTML-formatted responsive reading content.
        """
        lines = []
        for row in range(self.table.rowCount()):
            speaker_item = self.table.item(row, 0)
            response_item = self.table.item(row, 1)
            if speaker_item and response_item:
                speaker = speaker_item.text().strip()
                response = response_item.text().strip()
                lines.append(f"<b>{speaker}:</b> {response}")
        return "\n".join(lines)

    def save_respo_json(self):
        """
        Save the current responsive reading data to a JSON file.

        The data is written back to the file corresponding to the selected
        responsive reading number under `data/respo/`. A warning is shown
        if no valid number is provided.
        """
        num = self.number_input.text().strip()
        if not num.isdigit():
            QMessageBox.warning(self, "저장 오류", "먼저 번호를 입력하고 데이터를 불러오세요.")
            return

        path = os.path.join("data", "respo", f"responsive_{int(num):03d}.json")
        self.respo_data["title"] = self.capt_edit.text()
        slides = []
        for row in range(self.table.rowCount()):
            speaker_item = self.table.item(row, 0)
            hdln_item = self.table.item(row, 1)
            if speaker_item and hdln_item:
                slides.append({
                    "speaker": speaker_item.text(),
                    "headline": hdln_item.text()
                })
        self.respo_data["slides"] = slides

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.respo_data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "저장 완료", f"새교독문 {num}번의 데이터베이스를 업데이트하였습니다.")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"파일을 저장할 수 없습니다:\n{path}")