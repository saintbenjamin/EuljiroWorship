# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/settings_dialog.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Settings dialog for the slide generator and controller.

This module defines :class:`core.generator.ui.settings_dialog.SettingsDialog`, a modal dialog that allows users to
configure persistent UI-related settings shared by the slide generator
(and controller), including:

- Font family
- Font size
- Font weight
- Output path for the emergency subtitle file (e.g., ``verse_output.txt``)

Settings are stored in a JSON file at a well-defined location and are
loaded automatically when the dialog is opened.
"""

import os
import json

from PySide6.QtWidgets import (
    QDialog, QLabel, QFontComboBox, QSpinBox, QComboBox,
    QLineEdit, QPushButton, QFileDialog, QHBoxLayout,
    QVBoxLayout
)
from PySide6.QtGui import QFont

from core.config import paths

SETTINGS_PATH = paths.SETTING_FILE

class SettingsDialog(QDialog):
    """
    Dialog for configuring generator and controller settings.

    This dialog provides controls for selecting font preferences used
    throughout the generator/controller UI and for specifying the file
    path of the emergency subtitle output file.

    The dialog follows a simple lifecycle:

    - Load persisted settings on construction.
    - Allow the user to modify values via UI controls.
    - Persist updated settings when accepted.

    Attributes:
        font_combo (QFontComboBox):
            Font family selector.
        size_spin (QSpinBox):
            Font size selector.
        weight_combo (QComboBox):
            Font weight selector.
        path_line (QLineEdit):
            Text field for the emergency subtitle file path.
    """

    def __init__(self, parent=None):
        """
        Initialize the settings dialog.

        This constructor builds the full UI layout, initializes all input
        widgets, and loads previously saved settings from the persistent
        settings file into the UI.

        Args:
            parent (QWidget | None):
                Optional parent widget for modal ownership.

        Returns:
            None
        """
        super().__init__(parent)
        self.setWindowTitle("대한예수교장로회(통합) 을지로교회 슬라이드 제너레이터/컨트롤러 설정")
        self.resize(400, 250)

        # ───────────── Font settings widgets ─────────────
        self.font_label = QLabel("글꼴 종류")
        self.font_combo = QFontComboBox()

        self.size_label = QLabel("글꼴 크기")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)

        self.weight_label = QLabel("글꼴 굵기")
        self.weight_combo = QComboBox()
        self.weight_combo.addItem("Thin", QFont.Weight.Thin)
        self.weight_combo.addItem("ExtraLight", QFont.Weight.ExtraLight)
        self.weight_combo.addItem("Light", QFont.Weight.Light)
        self.weight_combo.addItem("Normal", QFont.Weight.Normal)
        self.weight_combo.addItem("Medium", QFont.Weight.Medium)
        self.weight_combo.addItem("DemiBold", QFont.Weight.DemiBold)
        self.weight_combo.addItem("Bold", QFont.Weight.Bold)
        self.weight_combo.addItem("ExtraBold", QFont.Weight.ExtraBold)
        self.weight_combo.addItem("Black", QFont.Weight.Black)

        # ───────────── Emergency caption file path input ─────────────
        self.path_label = QLabel("긴급자막 파일 위치")
        self.path_line = QLineEdit()
        self.browse_btn = QPushButton("찾아보기")
        self.browse_btn.clicked.connect(self.browse_path)

        # ───────────── Dialog buttons ─────────────
        self.ok_btn = QPushButton("확인")
        self.cancel_btn = QPushButton("취소")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # ───────────── Layout construction ─────────────
        layout = QVBoxLayout()
        layout.addWidget(self.font_label)
        layout.addWidget(self.font_combo)
        layout.addWidget(self.size_label)
        layout.addWidget(self.size_spin)
        layout.addWidget(self.weight_label)
        layout.addWidget(self.weight_combo)
        layout.addWidget(self.path_label)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_line)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_settings()

    def browse_path(self):
        """
        Open a file dialog to select the emergency subtitle output file.

        This method shows a file-open dialog filtered to text files and, if
        the user selects a file, updates the corresponding path input field.

        Args:
            None

        Returns:
            None
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "긴급자막 파일 선택", "", "Text Files (*.txt)")
        if file_path:
            self.path_line.setText(file_path)

    def load_settings(self):
        """
        Load persisted settings from the JSON settings file into the UI.

        If the settings file exists, this method reads the JSON content and
        updates the font selectors and emergency subtitle path field.
        If the file does not exist, default values remain in effect.

        Args:
            None

        Returns:
            None

        Raises:
            json.JSONDecodeError:
                If the settings file exists but contains invalid JSON.
            OSError:
                If the settings file cannot be read.
        """
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.font_combo.setCurrentText(settings.get("font_family", ""))
                self.size_spin.setValue(settings.get("font_size", 24))
                self.weight_combo.setCurrentText(settings.get("font_weight", "Normal"))
                self.path_line.setText(settings.get("verse_output_path", ""))

    def save_settings(self) -> dict:
        """
        Persist the current settings to the JSON settings file.

        This method collects values from the UI controls, writes them to the
        settings file in UTF-8 encoded JSON format, and returns the saved
        settings dictionary.

        Args:
            None

        Returns:
            dict:
                Dictionary containing the persisted settings, including font
                preferences and the emergency subtitle file path.

        Raises:
            OSError:
                If the settings file cannot be written.
        """
        settings = {
            "font_family": self.font_combo.currentText(),
            "font_size": self.size_spin.value(),
            "font_weight": self.weight_combo.currentText(),
            "verse_output_path": self.path_line.text()
        }
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return settings