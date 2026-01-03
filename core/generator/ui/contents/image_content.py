# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/contents/image_content.py

UI content widget for editing 'image' style slides.

This module defines `ImageContent`, a QWidget that allows users to select
an image file, preview it, and associate it with caption text for use
in image-based slides. Selected images are copied into a local `img/`
directory for reliable access by overlay HTML files.

In this slide style, the `headline` field is repurposed to store the
relative image path, while the `caption` field is used as accompanying
text displayed alongside the image.

The widget integrates with `SlideInputSubmitter` to support automatic
submission and synchronization with the parent generator window.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
import shutil
from core.generator.utils.slide_input_submitter import SlideInputSubmitter

class ImageContent(QWidget):
    """
    Content editor widget for 'image' style slides.

    This widget allows users to:
    - Select an image file from disk
    - Copy the selected image into a local image directory for overlay use
    - Preview the selected image
    - Enter optional caption text associated with the image

    In this slide style, the image path is stored in the `headline` field
    of the slide data dictionary, while the `caption` field contains
    accompanying text.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the image content editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator window, used for submitting slide data
                and enabling auto-save behavior.
            caption (str):
                Initial caption text associated with the image.
            headline (str):
                Initial image path (stored in the headline field).

        Returns:
            None
        """
        super().__init__(parent)
        self.caption = caption
        self.headline = headline  # Here, 'headline' will now store the image path
        self.generator_window = generator_window
        self.build_ui()

    def build_ui(self):
        """
        Construct the UI elements for editing an image slide.

        This method builds input fields for caption and image path, a button
        for selecting an image file, and an image preview area. It also
        registers the input fields with `SlideInputSubmitter` to enable
        automatic submission.

        Args:
            None

        Returns:
            None
        """
        layout = QVBoxLayout(self)

        # Headline input (now stores image path)
        self.headline_label = QLabel("제목 (이미지 경로 저장)")
        self.headline_edit = QLineEdit(self.headline)

        # Caption input
        self.caption_label = QLabel("부제")
        self.caption_edit = QLineEdit(self.caption)

        # Image selection button
        self.image_button = QPushButton("그림 선택")
        self.image_button.clicked.connect(self.select_image)

        # Image preview
        self.image_preview = QLabel("선택된 그림 없음")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setFixedHeight(200)
        self.image_preview.setScaledContents(True)

        layout.addWidget(self.headline_label)
        layout.addWidget(self.headline_edit)
        layout.addWidget(self.caption_label)
        layout.addWidget(self.caption_edit)
        layout.addWidget(self.image_button)
        layout.addWidget(self.image_preview)
        layout.addStretch()

        self.setLayout(layout)

        # Auto-submit support
        inputs = {
            "title": self.caption_edit,
            "body": self.headline_edit  # Now 'body' is storing the image path
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_image_slide)

    def select_image(self):
        """
        Prompt the user to select an image file and register it for slide use.

        The selected image is copied into the local image directory and its
        relative path is stored in the headline field. A preview of the image
        is displayed in the UI.

        Args:
            None

        Returns:
            None
        """
        path, _ = QFileDialog.getOpenFileName(self, "그림 선택", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            relative_path = self.copy_to_img_folder(path)
            # 경로 구분자를 자동으로 '/'로 변경
            self.headline = relative_path.replace("\\", "/")
            self.headline_edit.setText(self.headline)  # Update the headline field with the path
            pixmap = QPixmap(path)
            self.image_preview.setPixmap(pixmap)
            self.image_preview.setToolTip(path)

    def copy_to_img_folder(self, source_path: str) -> str:
        """
        Copy the selected image file into the local image directory.

        If the destination directory does not exist, it is created. If the
        image already exists at the destination, it is not copied again.

        Args:
            source_path (str):
                Absolute path to the source image file.

        Returns:
            str:
                Relative image path suitable for use in overlay HTML
                (e.g., "img/example.png").

        Raises:
            OSError:
                If the file cannot be copied or the destination directory
                cannot be created.
        """
        overlay_root = "."  # assume current working directory contains overlay_hall.html
        img_dir = os.path.join(overlay_root, "html", "img")
        os.makedirs(img_dir, exist_ok=True)

        fname = os.path.basename(source_path)
        dest_path = os.path.join(img_dir, fname)

        if not os.path.exists(dest_path):
            shutil.copy2(source_path, dest_path)

        return os.path.join("img", fname)

    def build_image_slide(self):
        """
        Conditionally generate image slide data.

        If no image path has been selected, no slide data is generated.
        Otherwise, the current inputs are returned as a slide data dictionary.

        Args:
            None

        Returns:
            dict | None:
                Slide data dictionary if an image is selected; otherwise, None.
        """
        data = self.get_slide_data()
        if not data["headline"]:  # headline now holds the image path
            return None
        return data

    def get_slide_data(self) -> dict:
        """
        Generate the slide data dictionary for an image slide.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the image slide, including:
                - style
                - caption
                - headline (relative image path)
        """
        return {
            "style": "image",
            "caption": self.caption_edit.text().strip(),
            "headline": self.headline_edit.text().strip()  # Store image path here
        }

    def set_content(self, data: dict):
        """
        Restore saved image slide data into the editor UI.

        This method populates the caption and image path fields and attempts
        to load and preview the referenced image.

        Args:
            data (dict):
                Slide data dictionary containing caption and image path.

        Returns:
            None
        """
        self.caption_edit.setText(data.get("caption", ""))
        self.headline = data.get("headline", "")
        self.headline_edit.setText(self.headline)  # 'headline' now contains image path
        print(self.headline)
        if self.headline:
            try:
                pixmap = QPixmap(self.headline)  # Use the image path in 'headline' to load the image
                self.image_preview.setPixmap(pixmap)
            except Exception:
                self.image_preview.setText("그림 로딩 실패")