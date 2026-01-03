# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/slide_generator_ui_builder.py

UI builder for the Slide Generator main window.

This module defines `SlideGeneratorUIBuilder`, a helper class responsible for
constructing and wiring the full Qt UI layout of the slide generator window.
It separates UI composition from application logic to keep the main window
class (`SlideGenerator`) focused on workflow and state management.

The builder assembles:
- A top row of action buttons with icons (load, save, add, insert, delete, move, export)
- A central table area for listing and managing slides
- A label showing the current worship/session name
- A menu bar entry for accessing generator settings
- Keyboard shortcuts (e.g., Ctrl+S) and signal connections

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QSizePolicy, QLabel
)
from PySide6.QtGui import QKeySequence, QShortcut, QAction

from core.generator.utils.icon_helpers import set_svg_icon, get_icon_path

class SlideGeneratorUIBuilder:
    """
    Build and wire the full UI layout for the slide generator window.

    This builder is responsible for composing the visual layout and connecting
    UI controls to the corresponding handlers exposed by the parent window.
    It does not own application state; instead, it assumes that the parent
    provides the necessary widgets and methods.

    Constructed UI elements
    -----------------------
    - A horizontal toolbar of action buttons (with SVG icons)
    - A label displaying the current worship/session name
    - The central slide table widget
    - A 'Tools > Settings' menu entry
    - Keyboard shortcuts and signal-slot connections

    Required parent interface
    -------------------------
    The parent object is expected to provide at least:
    - `table` (QTableWidget): main slide table widget
    - `menuBar()` -> QMenuBar
    - `table_manager`: row manipulation logic
    - `load_from_file()`: load slide session
    - `save_as()`: save slide session
    - `export_slides_for_overlay()`: export overlay JSON
    - `open_settings_dialog()`: open settings dialog
    - `handle_table_double_click(row, column)`: edit slide dialog
    - `apply_generator_font_settings()`: apply font preferences
    """
    def __init__(self, parent, worship_name=""):
        """
        Initialize the UI builder and immediately construct the UI layout.

        This constructor stores references to the parent window and the initial
        worship/session name, then calls `setup_ui()` to build and connect all
        UI components.

        Args:
            parent (QMainWindow or QWidget):
                The main SlideGenerator window that owns the UI and application logic.
                It must expose the methods and attributes required by this builder.
            worship_name (str):
                Initial worship/session name to display above the slide table.

        Returns:
            None
        """
        self.parent = parent
        self.worship_name = worship_name
        self.setup_ui()

    def setup_ui(self):
        """
        Construct and wire the complete slide generator UI.

        This method performs the following:
        - Registers keyboard shortcuts (e.g., Ctrl+S for saving)
        - Creates action buttons with SVG icons and connects them to parent handlers
        - Assembles the button toolbar, label, and slide table into a vertical layout
        - Adds a 'Tools > Settings' menu entry to the menu bar
        - Applies persisted font settings to the UI
        - Connects table double-click events to the slide editor dialog
        - Installs the composed layout as the parent's central widget

        Args:
            None

        Returns:
            None
        """
        parent = self.parent

        # Assign Ctrl+S to trigger save operation
        QShortcut(QKeySequence("Ctrl+S"), parent).activated.connect(parent.handle_ctrl_s)

        # Generator action buttons with SVG icons
        load_btn = QPushButton()
        set_svg_icon(load_btn, get_icon_path("load.svg"), size=30)
        save_btn = QPushButton()
        set_svg_icon(save_btn, get_icon_path("save.svg"), size=30)
        add_btn = QPushButton()
        set_svg_icon(add_btn, get_icon_path("add.svg"), size=30)
        insert_above_btn = QPushButton()
        set_svg_icon(insert_above_btn, get_icon_path("insert_above.svg"), size=30)
        insert_below_btn = QPushButton()
        set_svg_icon(insert_below_btn, get_icon_path("insert_below.svg"), size=30)
        del_btn = QPushButton()
        set_svg_icon(del_btn, get_icon_path("del.svg"), size=30)
        up_btn = QPushButton()
        set_svg_icon(up_btn, get_icon_path("up.svg"), size=30)
        down_btn = QPushButton()
        set_svg_icon(down_btn, get_icon_path("down.svg"), size=30)
        export_btn = QPushButton()
        set_svg_icon(export_btn, get_icon_path("export.svg"), size=30)

        # Apply consistent button height and layout policy
        for btn in [load_btn, save_btn, add_btn, insert_above_btn,
                    insert_below_btn, del_btn, up_btn, down_btn]:
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            btn.setMinimumHeight(28)

        # Connect button actions to parent handlers
        load_btn.clicked.connect(parent.load_from_file)
        save_btn.clicked.connect(parent.save_as)
        add_btn.clicked.connect(parent.table_manager.add_row)
        insert_above_btn.clicked.connect(lambda: parent.table_manager.insert_row(above=True))
        insert_below_btn.clicked.connect(lambda: parent.table_manager.insert_row(above=False))
        del_btn.clicked.connect(parent.table_manager.delete_selected_row)
        up_btn.clicked.connect(parent.table_manager.move_row_up)
        down_btn.clicked.connect(parent.table_manager.move_row_down)
        export_btn.clicked.connect(parent.export_slides_for_overlay)

        # Arrange buttons horizontally
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 2, 4, 2)
        btn_layout.setSpacing(4)
        for btn in [load_btn, save_btn, add_btn, insert_above_btn,
                    insert_below_btn, del_btn, up_btn, down_btn, export_btn]:
            btn_layout.addWidget(btn)

        # Wrap button layout in a QWidget container
        btn_container = QWidget()
        btn_container.setLayout(btn_layout)
        btn_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        # Worship name label (used as section title)
        self.worship_label = QLabel(self.worship_name)

        # Allow the table to expand and fill available space
        parent.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Final vertical layout assembly
        main_layout = QVBoxLayout()
        main_layout.addWidget(btn_container, 0)
        main_layout.addWidget(self.worship_label, 0)
        main_layout.addWidget(parent.table, 1)

        # Create 'Tools > Settings' menu
        menubar = parent.menuBar()
        tool_menu = menubar.addMenu("도구")
        settings_action = QAction("설정", parent)
        settings_action.triggered.connect(parent.open_settings_dialog)
        tool_menu.addAction(settings_action)

        # Apply saved font settings (from user config)
        parent.apply_generator_font_settings()

        # Link double-click on table rows to editor dialog
        parent.table.cellDoubleClicked.connect(parent.handle_table_double_click)

        # Wrap layout into a central widget
        central = QWidget()
        central.setLayout(main_layout)
        parent.setCentralWidget(central)

    def set_worship_label(self, name: str):
        """
        Update the worship/session name label shown above the slide table.

        This method is typically called after loading a session file or when the
        session name changes, and simply updates the text of the label if it exists.

        Args:
            name (str):
                New name to display (e.g., a worship title derived from the filename).

        Returns:
            None
        """
        if hasattr(self, "worship_label"):
            self.worship_label.setText(name)