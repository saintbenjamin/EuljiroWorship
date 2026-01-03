# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/contents/video_content.py

UI content widget for editing 'video' style slides.

This module defines `VideoContent`, a QWidget that allows users to select
a video file, preview it, and associate it with caption text for use
in video-based slides. Selected videos are copied into a local `html/img/`
directory for reliable access by overlay HTML files.

In this slide style, the `headline` field is repurposed to store the
relative video path, while the `caption` field is used as accompanying
text displayed alongside the video.

The widget integrates with `SlideInputSubmitter` to support automatic
submission and synchronization with the parent generator window.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import os
import shutil

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QLineEdit,
)
from PySide6.QtCore import Qt, QUrl

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from core.generator.utils.slide_input_submitter import SlideInputSubmitter


class VideoContent(QWidget):
    """
    Content editor widget for 'video' style slides.

    This widget allows users to:
    - Select a video file from disk
    - Copy the selected video into a local image directory for overlay use (html/img)
    - Preview the selected video (play/pause)
    - Enter optional caption text associated with the video

    In this slide style, the video path is stored in the `headline` field
    of the slide data dictionary, while the `caption` field contains
    accompanying text.
    """

    def __init__(self, parent, generator_window, caption: str = "", headline: str = ""):
        """
        Initialize the video content editor.

        Args:
            parent (QWidget):
                Parent widget container.
            generator_window:
                Reference to the generator window, used for submitting slide data
                and enabling auto-save behavior.
            caption (str):
                Initial caption text associated with the video.
            headline (str):
                Initial video path (stored in the headline field).

        Returns:
            None
        """
        super().__init__(parent)
        self.caption = caption
        self.headline = headline  # headline stores relative video path (e.g., "img/foo.mp4")
        self.generator_window = generator_window

        self.player = None
        self.audio = None
        self.video_widget = None

        self.build_ui()
        self._init_player()

        # If we were given an initial path, try to preview it.
        if self.headline:
            self._load_preview_from_relative_path(self.headline)

    def build_ui(self):
        """
        Construct the UI elements for editing a video slide.

        Builds input fields for caption and video path, a button for selecting
        a video file, and a video preview area. Registers the input fields with
        `SlideInputSubmitter` to enable automatic submission.

        Returns:
            None
        """
        layout = QVBoxLayout(self)

        # Headline input (stores video path)
        self.headline_label = QLabel("제목 (비디오 경로 저장)")
        self.headline_edit = QLineEdit(self.headline)

        # Caption input
        self.caption_label = QLabel("부제")
        self.caption_edit = QLineEdit(self.caption)

        # Video selection button
        self.video_button = QPushButton("비디오 선택")
        self.video_button.clicked.connect(self.select_video)

        # Preview area
        self.preview_label = QLabel("선택된 비디오 없음")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(240)

        # Controls
        controls = QHBoxLayout()
        self.play_button = QPushButton("재생")
        self.pause_button = QPushButton("일시정지")
        self.stop_button = QPushButton("정지")

        self.play_button.clicked.connect(self.play_preview)
        self.pause_button.clicked.connect(self.pause_preview)
        self.stop_button.clicked.connect(self.stop_preview)

        controls.addWidget(self.play_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.stop_button)

        layout.addWidget(self.headline_label)
        layout.addWidget(self.headline_edit)
        layout.addWidget(self.caption_label)
        layout.addWidget(self.caption_edit)
        layout.addWidget(self.video_button)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.video_widget)
        layout.addLayout(controls)
        layout.addStretch()

        self.setLayout(layout)

        # Auto-submit support
        inputs = {
            "title": self.caption_edit,
            "body": self.headline_edit,  # body stores the relative video path
        }
        self.submitter = SlideInputSubmitter(inputs, self.generator_window, self.build_video_slide)

    def _init_player(self):
        """
        Initialize QMediaPlayer for in-widget preview.

        Returns:
            None
        """
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)

    def select_video(self):
        """
        Prompt the user to select a video file and register it for slide use.

        The selected video is copied into the local `html/img` directory and its
        relative path is stored in the headline field.

        Returns:
            None
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "비디오 선택",
            "",
            "Videos (*.mp4 *.mov *.m4v *.webm *.mkv *.avi)",
        )
        if not path:
            return

        relative_path = self.copy_to_img_folder(path)

        # Normalize separators to '/' for HTML compatibility.
        self.headline = relative_path.replace("\\", "/")
        self.headline_edit.setText(self.headline)

        self.preview_label.setText(os.path.basename(path))
        self.preview_label.setToolTip(path)

        self._load_preview_from_absolute_path(path)

    def copy_to_img_folder(self, source_path: str) -> str:
        """
        Copy the selected video file into the local image directory (html/img).

        If the destination directory does not exist, it is created.
        If the file already exists at the destination, it is not copied again.

        Args:
            source_path (str):
                Absolute path to the source video file.

        Returns:
            str:
                Relative path for overlay HTML usage, e.g. "img/example.mp4".

        Raises:
            OSError:
                If the file cannot be copied or the destination directory cannot be created.
        """
        overlay_root = "."  # assume current working directory contains html/...
        img_dir = os.path.join(overlay_root, "html", "img")
        os.makedirs(img_dir, exist_ok=True)

        fname = os.path.basename(source_path)
        dest_path = os.path.join(img_dir, fname)

        if not os.path.exists(dest_path):
            shutil.copy2(source_path, dest_path)

        return os.path.join("img", fname)

    def _load_preview_from_absolute_path(self, abs_path: str):
        """
        Load preview video into QMediaPlayer from an absolute file path.

        Args:
            abs_path (str): Absolute file path.

        Returns:
            None
        """
        try:
            url = QUrl.fromLocalFile(abs_path)
            self.player.setSource(url)
        except Exception:
            self.preview_label.setText("비디오 로딩 실패")

    def _load_preview_from_relative_path(self, rel_path: str):
        """
        Load preview video into QMediaPlayer from a relative path like "img/foo.mp4".

        This resolves it against "./html/" to match the copy destination.

        Args:
            rel_path (str): Relative path stored in slide data.

        Returns:
            None
        """
        try:
            # rel_path is like "img/foo.mp4" and real file is "./html/img/foo.mp4"
            abs_path = os.path.abspath(os.path.join(".", "html", rel_path))
            if os.path.exists(abs_path):
                self._load_preview_from_absolute_path(abs_path)
                self.preview_label.setText(os.path.basename(abs_path))
            else:
                self.preview_label.setText("비디오 파일 없음")
        except Exception:
            self.preview_label.setText("비디오 로딩 실패")

    def play_preview(self):
        """
        Start playing the preview video.

        Returns:
            None
        """
        if self.player:
            self.player.play()

    def pause_preview(self):
        """
        Pause the preview video.

        Returns:
            None
        """
        if self.player:
            self.player.pause()

    def stop_preview(self):
        """
        Stop the preview video.

        Returns:
            None
        """
        if self.player:
            self.player.stop()

    def build_video_slide(self):
        """
        Conditionally generate video slide data.

        If no video path has been selected, no slide data is generated.

        Returns:
            dict | None:
                Slide data dictionary if a video is selected; otherwise, None.
        """
        data = self.get_slide_data()
        if not data["headline"]:
            return None
        return data

    def get_slide_data(self) -> dict:
        """
        Generate the slide data dictionary for a video slide.

        Returns:
            dict:
                Dictionary representing the video slide:
                - style
                - caption
                - headline (relative video path, e.g., "img/foo.mp4")
        """
        return {
            "style": "video",
            "caption": self.caption_edit.text().strip(),
            "headline": self.headline_edit.text().strip(),
        }

    def set_content(self, data: dict):
        """
        Restore saved video slide data into the editor UI.

        Populates caption and video path fields and attempts to load preview.

        Args:
            data (dict):
                Slide data dictionary containing caption and video path.

        Returns:
            None
        """
        self.caption_edit.setText(data.get("caption", ""))
        self.headline = data.get("headline", "")
        self.headline_edit.setText(self.headline)

        if self.headline:
            self._load_preview_from_relative_path(self.headline)
        else:
            self.preview_label.setText("선택된 비디오 없음")
            if self.player:
                self.player.stop()
                self.player.setSource(QUrl())