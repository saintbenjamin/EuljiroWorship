# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/slide_generator_ui_builder.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

UI builder for the Slide Generator main window.

This module defines :class:`core.generator.ui.slide_generator_ui_builder.SlideGeneratorUIBuilder`, a helper class responsible for
constructing and wiring the full Qt UI layout of the slide generator window.
It separates UI composition from application logic to keep the main window
class (:class:`core.generator.ui.slide_generator.SlideGenerator`) focused on workflow and state management.

The builder assembles:

- A top row of action buttons with icons (load, save, add, duplicate, insert, delete, move, export)
- A tools menu containing church-specific Sunday worship-order actions,
  afternoon praise-service actions, announcement import actions, and settings
- A central table area for listing and managing slides
- A label showing the current worship/session name
- Keyboard shortcuts (e.g., Ctrl+S) and signal connections
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
    UI controls to handler methods exposed by the parent generator window.
    It does not own or manage application state; instead, it assumes that the
    parent provides the required widgets, managers, and callbacks.

    Constructed UI elements include:

    - A horizontal toolbar of action buttons (SVG-icon buttons), including row duplication
    - A label displaying the current worship/session name
    - The central slide table widget
    - ``도구`` menu actions for church-specific Sunday worship-order actions,
      afternoon praise-service actions, announcement import actions, and
      settings
    - Keyboard shortcuts and signal-slot connections

    Required parent interface:

    The parent object is expected to provide at least:

    - ``table`` (QTableWidget):
        Main slide table widget.
    - ``menuBar()`` -> QMenuBar:
        Menu bar accessor for adding menus and actions.
    - ``table_manager`` (core.generator.ui.slide_table_manager.SlideTableManager):
        Row manipulation logic for the slide table, including insertion,
        deletion, movement, and duplication.
    - ``prompt_load_from_file()``:
        Run the interactive file-open flow and load a slide session.
    - ``save_as()``:
        Save the current slide session using a Save As flow.
    - ``export_slides_for_overlay()``:
        Export overlay-ready JSON and launch the slide controller if needed.
    - ``import_worship_order_and_announcements_from_hwpx()``:
        Import both worship-order information and announcement slides from a
        single HWPX bulletin file.
    - ``import_worship_order_from_hwpx()``:
        Import worship-order information from a HWPX bulletin file.
    - ``import_praise_service_order_and_announcements_from_hwpx()``:
        Import both afternoon praise-service order information and
        announcement slides from a single HWPX bulletin file.
    - ``import_praise_service_order_from_hwpx()``:
        Import afternoon praise-service order information from a HWPX bulletin file.
    - ``import_announcements()``:
        Import announcement slides from another worship JSON file.
    - ``import_announcements_from_hwpx()``:
        Import announcement slides from a HWPX bulletin file.
    - ``handle_ctrl_s()``:
        Handle the Ctrl+S shortcut for saving the current session.
    - ``open_settings_dialog()``:
        Open the generator settings dialog.
    - ``handle_table_double_click(row: int, column: int)``:
        Open the style-specific slide editor dialog.
    - ``apply_generator_font_settings()``:
        Apply persisted font preferences to the generator UI.

    Attributes:
        parent (QMainWindow | QWidget):
            The slide generator main window that owns the UI and application logic.
            All widgets are ultimately attached to this object.
        worship_name (str):
            Current worship/session name displayed above the slide table.
        worship_label (QLabel):
            Label widget showing the current worship/session name. This is created
            during UI setup and updated when a session is loaded or renamed.
    """

    def __init__(self, parent, worship_name=""):
        """
        Initialize the UI builder and immediately construct the UI layout.

        This constructor stores references to the parent window and the initial
        worship/session name, then calls :meth:`setup_ui` to build and connect all
        UI components.

        Args:
            parent (QMainWindow or QWidget):
                The main :class:`core.generator.ui.slide_generator.SlideGenerator` window that owns the UI and application logic.
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
        - Provides direct row actions such as add, duplicate, insert, delete, and move
        - Assembles the button toolbar, label, and slide table into a vertical layout
        - Adds grouped church-specific Sunday worship-order, afternoon
          praise-service, announcement import, and settings actions to the
          Tools menu
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
        duplicate_btn = QPushButton()
        set_svg_icon(duplicate_btn, get_icon_path("clone.svg"), size=30)
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
        for btn in [load_btn, save_btn, add_btn, duplicate_btn, insert_above_btn,
                    insert_below_btn, del_btn, up_btn, down_btn, export_btn]:
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            btn.setMinimumHeight(28)

        # Connect button actions to parent handlers
        load_btn.clicked.connect(parent.prompt_load_from_file)
        save_btn.clicked.connect(parent.save_as)
        add_btn.clicked.connect(parent.table_manager.add_row)
        duplicate_btn.clicked.connect(parent.table_manager.duplicate_selected_row)
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
        for btn in [load_btn, save_btn, add_btn, duplicate_btn, insert_above_btn,
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

        # Create 'Tools' menu
        menubar = parent.menuBar()
        tool_menu = menubar.addMenu("도구")

        hwpx_worship_order_action = QAction("HWPX 예배순서 가져오기 (을지로교회 전용)", parent)
        hwpx_worship_order_action.triggered.connect(parent.import_worship_order_from_hwpx)
        tool_menu.addAction(hwpx_worship_order_action)

        hwpx_full_action = QAction("HWPX 예배순서+광고 가져오기 (을지로교회 전용)", parent)
        hwpx_full_action.triggered.connect(parent.import_worship_order_and_announcements_from_hwpx)
        tool_menu.addAction(hwpx_full_action)

        tool_menu.addSeparator()

        hwpx_praise_service_action = QAction("HWPX 오후찬양예배 순서 가져오기 (을지로교회 전용)", parent)
        hwpx_praise_service_action.triggered.connect(parent.import_praise_service_order_from_hwpx)
        tool_menu.addAction(hwpx_praise_service_action)

        hwpx_praise_service_full_action = QAction("HWPX 오후찬양예배 순서+광고 가져오기 (을지로교회 전용)", parent)
        hwpx_praise_service_full_action.triggered.connect(parent.import_praise_service_order_and_announcements_from_hwpx)
        tool_menu.addAction(hwpx_praise_service_full_action)

        tool_menu.addSeparator()

        hwpx_announcement_action = QAction("HWPX 광고 가져오기 (을지로교회 전용)", parent)
        hwpx_announcement_action.triggered.connect(parent.import_announcements_from_hwpx)
        tool_menu.addAction(hwpx_announcement_action)

        import_announcements_action = QAction("JSON 광고 가져오기 (을지로교회 전용)", parent)
        import_announcements_action.triggered.connect(parent.import_announcements)
        tool_menu.addAction(import_announcements_action)

        tool_menu.addSeparator()

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
