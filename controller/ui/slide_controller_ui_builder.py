# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/controller/ui/slide_controller_ui_builder.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Builds the user interface for the slide controller window.

This module defines a small UI builder class that constructs and wires the
widgets used by the :class:`controller.slide_controller.SlideController` main window. The builder is responsible for
creating the layout, initializing interactive controls, populating the preview
table, and installing event filters for keyboard navigation.

Key responsibilities:

- Create top status label and apply elided text rendering
- Create emergency caption ON/OFF buttons and connect controller callbacks
- Create page navigation controls (first/prev/next/last + page input)
- Create and populate the slide preview table
- Install global event filters for keyboard-based slide navigation
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView,
    QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics

from core.generator.utils.icon_helpers import set_svg_icon, get_icon_path

class SlideControllerUIBuilder:
    """
    UI builder for the :class:`controller.slide_controller.SlideController` main window.

    This class encapsulates widget construction so that
    :class:`controller.slide_controller.SlideController` can keep runtime logic
    separate from UI layout details. The builder creates and attaches widgets
    onto the controller instance (``self.c``), and wires up signals to the
    controller's navigation and emergency-caption handlers.

    The builder assumes the controller already has:

    - ``slides``: list[dict] containing slide data for preview population
    - ``index``: int current slide index to pre-select in the table

    Attributes:
        c (controller.slide_controller.SlideController):
            The controller instance that owns the window and runtime logic.
            Widgets created by this builder are attached onto this object.

            This builder assigns (at minimum) the following attributes onto ``c``:

            - label (`QLabel <https://doc.qt.io/qt-6/qlabel.html>`_): Top status label (elided text).
            - btn_on (`QPushButton <https://doc.qt.io/qt-6/qpushbutton.html>`_): Emergency caption ON button.
            - btn_off (`QPushButton <https://doc.qt.io/qt-6/qpushbutton.html>`_): Emergency caption OFF button.
            - first_button (`QPushButton <https://doc.qt.io/qt-6/qpushbutton.html>`_): Jump to first slide button.
            - prev_button (`QPushButton <https://doc.qt.io/qt-6/qpushbutton.html>`_): Jump to previous slide button.
            - next_button (`QPushButton <https://doc.qt.io/qt-6/qpushbutton.html>`_): Jump to next slide button.
            - last_button (`QPushButton <https://doc.qt.io/qt-6/qpushbutton.html>`_): Jump to last slide button.
            - page_input (`QLineEdit <https://doc.qt.io/qt-6/qlineedit.html>`_): Page number input used for direct jump.
            - table (`QTableWidget <https://doc.qt.io/qt-6/qtablewidget.html>`_): Slide preview table (row selection + click-to-jump).

    Note:
        - Widgets are attached onto the controller instance as attributes
          (e.g., ``controller.label``, ``controller.table``, ``controller.page_input``).
        - The builder installs event filters on the controller and its table to
          support keyboard navigation.
    """

    def __init__(self, controller):
        """
        Initialize the UI builder with a :class:`controller.slide_controller.SlideController` instance.

        Args:
            controller (`QWidget <https://doc.qt.io/qt-6/qwidget.html>`_):
                The main :class:`controller.slide_controller.SlideController` instance that owns the window and runtime
                logic. Widgets created by this builder are assigned as attributes
                on this object.

        Returns:
            None
        """
        self.c = controller

    def build_ui(self):
        """
        Build and wire the full :class:`controller.slide_controller.SlideController` UI.

        This method constructs:

        - Top status label (with elided rendering)
        - Emergency caption ON/OFF buttons
        - Page navigation row (first/prev/page/next/last)
        - Slide preview table (row selection + click-to-jump)
        - Event filters for global keyboard navigation

        Side Effects:

        - Creates widgets and assigns them onto the controller instance.
        - Connects widget signals to controller slots/callbacks.
        - Installs event filters on the controller and its table.

        Returns:
            None
        """
        layout = QVBoxLayout(self.c)

        # ─────────────── Top label ───────────────
        self.c.label = QLabel("", self.c)
        self.c.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.set_elided_label_text(self.c.label, "")
        layout.addWidget(self.c.label)

        # ─────────────── Emergency caption buttons ───────────────
        self.c.btn_on = QPushButton()
        set_svg_icon(self.c.btn_on, get_icon_path("emergency.svg"), size=30, text=" ON")
        self.c.btn_on.clicked.connect(self.c.launch_emergency_caption)
        layout.addWidget(self.c.btn_on)

        self.c.btn_off = QPushButton()
        set_svg_icon(self.c.btn_off, get_icon_path("emergency.svg"), size=30, text=" OFF")
        self.c.btn_off.clicked.connect(self.c.clear_emergency_caption)
        layout.addWidget(self.c.btn_off)

        # ─────────────── Page number and navigation ───────────────
        jump_layout = QHBoxLayout()

        self.c.first_button = QPushButton()
        set_svg_icon(self.c.first_button, get_icon_path("first.svg"), size=30)
        self.c.prev_button = QPushButton()
        set_svg_icon(self.c.prev_button, get_icon_path("prev.svg"), size=30)
        self.c.next_button = QPushButton()
        set_svg_icon(self.c.next_button, get_icon_path("next.svg"), size=30)
        self.c.last_button = QPushButton()
        set_svg_icon(self.c.last_button, get_icon_path("last.svg"), size=30)

        self.c.first_button.clicked.connect(lambda: self.c.jump_to_index(0))
        self.c.prev_button.clicked.connect(self.c.jump_to_previous)
        self.c.next_button.clicked.connect(self.c.jump_to_next)
        self.c.last_button.clicked.connect(lambda: self.c.jump_to_index(len(self.c.slides) - 1))

        for btn in [self.c.first_button, self.c.prev_button, self.c.next_button, self.c.last_button]:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.c.page_input = QLineEdit()
        self.c.page_input.setPlaceholderText("Page")
        self.c.page_input.setFixedWidth(80)
        self.c.page_input.returnPressed.connect(self.c.jump_to_page)

        jump_layout.addWidget(self.c.first_button)
        jump_layout.addWidget(self.c.prev_button)
        jump_layout.addWidget(self.c.page_input)
        jump_layout.addWidget(self.c.next_button)
        jump_layout.addWidget(self.c.last_button)

        layout.addLayout(jump_layout)

        # ─────────────── Slide preview table ───────────────
        self.c.table = QTableWidget(0, 3)
        self.c.table.setHorizontalHeaderLabels(["", "제목", "본문"])
        self.c.table.verticalHeader().setDefaultSectionSize(50)
        self.c.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.c.table.setSelectionMode(QTableWidget.SingleSelection)
        self.c.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.c.table.verticalHeader().setVisible(False)

        # Populate table with slide previews
        for i, slide in enumerate(self.c.slides):
            self.c.table.insertRow(i)
            self.c.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.c.table.setItem(i, 1, QTableWidgetItem(slide.get("caption", "")))
            self.c.table.setItem(i, 2, QTableWidgetItem(slide.get("headline", "").split("\n")[0][:50]))

        # Pre-select current slide row
        self.c.table.selectRow(self.c.index)
        self.c.table.cellClicked.connect(self.c.on_cell_clicked)

        # ─────────────── Table column stretch configuration ───────────────
        header = self.c.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.c.table)

        # ─────────────── Event filter for keyboard control ───────────────
        self.c.setFocusPolicy(Qt.StrongFocus)
        self.c.installEventFilter(self.c)
        self.c.table.installEventFilter(self.c)

        self.c.setLayout(layout)

    @staticmethod
    def set_elided_label_text(label: QLabel, text: str):
        """
        Set right-elided text on a `QLabel <https://doc.qt.io/qt-6/qlabel.html>`_ to fit the current label width.

        This helper computes an elided string (truncated with an ellipsis) so the
        label does not overflow horizontally. Truncation occurs on the right side.

        Args:
            label (QLabel):
                Target label widget whose text will be updated.
            text (str):
                Full text to render (may be truncated).

        Returns:
            None
        """
        metrics = QFontMetrics(label.font())
        width = label.width() - 10  # Slight right margin
        elided = metrics.elidedText(text, Qt.ElideRight, width)
        label.setText(elided)