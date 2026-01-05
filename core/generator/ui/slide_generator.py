# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/slide_generator.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Main window class for the EuljiroWorship slide generator GUI.

This module defines the main Qt window (:class:`core.generator.ui.slide_generator.SlideGenerator`) that drives the
slide authoring workflow:

- Manage a table of slides (add/insert/delete/reorder).
- Edit slides via a style-specific modal editor dialog.
- Save/load a "session" JSON file for ongoing editing.
- Export overlay-ready slide JSON for the live controller/overlay.
- Open and apply persistent generator settings (fonts, paths, etc.).

The generator is typically launched from the project entry point
(``EuljiroWorship.py``) and interacts with a slide controller process
through exported JSON and the WebSocket-based overlay pipeline.
"""

import os
import datetime
import json

from PySide6.QtWidgets import (
    QMainWindow, QTableWidget, QWidget, 
    QFileDialog, QMessageBox, QHeaderView, 
    QAbstractItemView, QInputDialog, QDialog, 
    QTableWidgetItem
)
from PySide6.QtGui import QFont

from core.config import paths, style_map
from core.generator.settings_generator import load_generator_settings
from core.generator.settings_last_path import save_last_path
from core.generator.ui.settings_dialog import SettingsDialog
from core.generator.ui.slide_generator_ui_builder import SlideGeneratorUIBuilder
from core.generator.ui.slide_table_manager import SlideTableManager
from core.generator.utils.slide_exporter import SlideExporter
from core.generator.utils.slide_generator_data_manager import SlideGeneratorDataManager
from core.plugin.slide_controller_launcher import SlideControllerLauncher

class SlideGenerator(QMainWindow):
    """
    Main window for the EuljiroWorship slide generator.

    The generator provides a table-based slide session editor and supports:

    - Creating, inserting, deleting, and reordering slide rows
    - Editing each slide via a style-specific modal dialog (double-click)
    - Loading and saving slide sessions as JSON files
    - Exporting overlay-ready JSON (prepends a blank slide for a clean initial state)
    - Launching the slide controller for live output (if not already running)

    Core collaborators (high-level):

    - :class:`core.generator.ui.slide_table_manager.SlideTableManager`:
        Owns table row operations (add/insert/delete/move) for the main table widget.
    - :class:`core.generator.utils.slide_generator_data_manager.SlideGeneratorDataManager`:
        Loads/saves and collects slide session data from the table.
    - :class:`core.generator.ui.slide_generator_ui_builder.SlideGeneratorUIBuilder`:
        Builds and wires the generator window UI chrome (menus, buttons, labels).
    - :class:`core.generator.utils.slide_exporter.SlideExporter`:
        Converts the internal slide session into the overlay JSON format.
    - :class:`core.plugin.slide_controller_launcher.SlideControllerLauncher`:
        Launches the controller UI/process that pushes slides to the overlay target.

    Note:
        - On startup, this window may show a file-open dialog to load an existing
          session. If the user cancels, a blank session is created.
        - Table cells are intentionally non-editable; edits are performed via the
          modal per-style editor dialog.

    Attributes:
        first_save_done (bool):
            Tracks whether the first save action has completed in the current
            session. Used to choose between "save as" vs. save-to-last-path on
            Ctrl+S.
        reverse_style_aliases (dict[str, str]):
            Reverse mapping from the displayed style label (Korean UI text) to
            the internal style key (e.g., "가사" -> "lyrics"). Derived from
            ``style_map.REVERSE_ALIASES``.
        table (QTableWidget):
            Main slide table with three columns: style, caption, headline.
            Rows represent slides in the current session.
        detail_widget (QWidget):
            Right-side placeholder panel (reserved for future detail views).
        slide_controller_launcher (SlideControllerLauncher):
            Helper that launches (or detects) the running slide controller.
        table_manager (SlideTableManager):
            Encapsulates row operations and table manipulation logic.
        data_manager (SlideGeneratorDataManager):
            Loads/saves session JSON and collects session data from the table.
        ui_builder (SlideGeneratorUIBuilder):
            UI builder responsible for wiring menus, buttons, and header labels.
        worship_name (str | None):
            Session label derived from the loaded filename stem. None for a new
            unsaved session.
        last_saved_path (str | None):
            Last known save path for the current session. When set, normal save
            operations write to this path without prompting.
    """

    def __init__(self):
        """
        Construct the main generator window and initialize the UI state.

        This initializer:

        - Creates and configures the main slide table widget
        - Initializes core helper components (table manager, data manager, UI builder, launcher)
        - Prompts the user to load an existing slide session via an OS file dialog (if canceled, starts with a blank session)

        Args:
            None

        Returns:
            None
        """
        super().__init__()

        self.setWindowTitle("대한예수교장로회(통합) 을지로교회 예배 슬라이드 제너레이터")
        self.resize(1000, 600)

        self.first_save_done = False

        self.reverse_style_aliases = style_map.REVERSE_ALIASES

        # --- Left-side slide table setup ---
        self.table = QTableWidget(0, 3)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalHeaderLabels(["스타일", "소제목", "본문"])
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Adjust column resize behavior
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)

        # --- Right-side placeholder panel ---
        self.detail_widget = QWidget()

        # --- Core components ---
        self.slide_controller_launcher = SlideControllerLauncher()
        self.table_manager = SlideTableManager(self.table, self)
        self.data_manager = SlideGeneratorDataManager(self.table)
        self.worship_name = None
        self.ui_builder = SlideGeneratorUIBuilder(self, self.worship_name)

        self.last_saved_path = None

        # Prompt is removed — instead, load file and extract name
        load_path = self.load_from_file()  # Shows OS file dialog on startup
        if load_path:
            filename_only = os.path.splitext(os.path.basename(load_path))[0]
            self.worship_name = filename_only
            self.ui_builder.set_worship_label(self.worship_name)
            self.last_saved_path = load_path
        else:
            self.table_manager.add_row()  # User cancelled → start blank
            self.worship_name = None
            self.ui_builder.set_worship_label("(No file loaded)")
 
        # Safety: disable in-place editing
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

    def save_slides_to_file(self, show_message=False):
        """
        Save the current slide session to the last saved path.

        If no previous save path exists, a timestamp-based filename is generated
        in the current working directory. The session data is collected from the
        table via :meth:`core.generator.utils.slide_generator_data_manager.SlideGeneratorDataManager.collect_slide_data()` and written
        as UTF-8 JSON.

        Args:
            show_message (bool):
                If True, shows a confirmation message box after saving.

        Returns:
            None
        """
        # Generate default filename if needed
        if not self.last_saved_path:
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.last_saved_path = f"{now}_slides.json"

        slide_data = self.data_manager.collect_slide_data()
        if slide_data:
            with open(self.last_saved_path, "w", encoding="utf-8") as f:
                json.dump(slide_data, f, ensure_ascii=False, indent=2)

            save_last_path(self.last_saved_path)

            if show_message:
                QMessageBox.information(self, "저장 완료", f"{self.last_saved_path} 로 저장되었습니다.")

    def handle_ctrl_s(self):
        """
        Handle the Ctrl+S shortcut for saving.

        Behavior:

        - If this is the first save in the current session (or no prior save path exists), triggers a "save as" flow that prompts the user for a path.
        - Otherwise, saves to the last known path and shows a confirmation dialog.

        Args:
            None

        Returns:
            None
        """
        if not self.first_save_done or not self.last_saved_path:
            self.save_to_file()
            self.first_save_done = True
        else:
            self.save_slides_to_file(show_message=True)

    def load_from_file(self, path=None):
        """
        Load a slide session JSON file into the generator.

        If ``path`` is None, an OS file-open dialog is shown. The initial directory
        is derived from the last opened file record (if available); otherwise the
        current working directory is used.

        After loading:

        - The table is populated via the data manager
        - The worship/session name label is updated from the filename stem
        - ``first_save_done`` is reset so the next Ctrl+S follows the intended flow

        Args:
            path (str | None):
                Absolute or relative path to the JSON file. If None, a dialog is shown.

        Returns:
            str | None:
                The resolved path that was loaded, or None if the user canceled the dialog
                or no file was selected.
        """
        import os
        import json

        if not path:
            # Try to read directory of last opened file
            try:
                with open(paths.SETTING_LAST_OPEN_FILE, encoding="utf-8") as f:
                    record = json.load(f)
                    last_path = record.get("last_opened_file", "")
                    if os.path.isfile(last_path):
                        default_dir = os.path.dirname(last_path)
                    else:
                        default_dir = os.getcwd()
            except Exception:
                default_dir = os.getcwd()

            # Prompt file dialog
            path, _ = QFileDialog.getOpenFileName(
                self,
                "불러올 파일 선택",
                default_dir,
                "JSON Files (*.json);;All Files (*)"
            )
            if not path:
                return None

        self.data_manager.load_from_file(path)
        filename_only = os.path.splitext(os.path.basename(path))[0]
        self.worship_name = filename_only
        self.ui_builder.set_worship_label(self.worship_name)
        self.first_save_done = False
        return path

    def save_as(self):
        """
        Save the current session using an explicit "Save As" dialog.

        This always forces the file-save dialog regardless of whether a previous
        save path exists.

        Args:
            None

        Returns:
            None
        """
        self.save_to_file(force_dialog=True)
        self.first_save_done = True

    def save_to_file(self, path=None, force_dialog=False):
        """
        Save the current slide session as a JSON file.

        Save destination selection rules:

        - If ``path`` is provided, saves directly to that path.
        - Else if ``force_dialog`` is False and ``self.last_saved_path`` exists, saves to ``self.last_saved_path`` without prompting.
        - Otherwise, opens an OS file-save dialog and saves to the chosen path.

        The slide session is collected via :meth:`core.generator.utils.slide_generator_data_manager.SlideGeneratorDataManager.collect_slide_data()`
        and written as UTF-8 JSON.

        Args:
            path (str | None):
                Destination file path. If None, follows the selection rules above.
            force_dialog (bool):
                If True, always shows the OS save dialog when ``path`` is None.

        Returns:
            None
        """
        import os
        import json

        # Force dialog even if last_saved_path exists
        if not path and not force_dialog and self.last_saved_path:
            path = self.last_saved_path

        if not path:
            default_name = f"{self.worship_name or 'worship'}.json"
            default_dir = os.path.dirname(self.last_saved_path) if self.last_saved_path else os.getcwd()
            default_path = os.path.join(default_dir, default_name)

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Slide File",
                default_path,
                "JSON Files (*.json);;All Files (*)"
            )
            if not path:
                return

        # Save
        slide_data = self.data_manager.collect_slide_data()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(slide_data, f, ensure_ascii=False, indent=2)

        self.last_saved_path = path

    def warn_if_controller_running(self):
        """
        Warn the user if the slide controller is currently running.

        If the controller is running, edits made in the generator may not be
        reflected in the live output until the controller is restarted. This
        method shows a warning dialog and signals whether editing should be blocked.

        Args:
            None

        Returns:
            bool:
                True if the controller is running (warning shown),
                False otherwise.
        """
        if self.slide_controller_launcher.is_running():
            QMessageBox.warning(
                self,
                "편집 불가",
                "현재 슬라이드 컨트롤러가 실행 중입니다.\n"
                "편집 내용은 출력에 반영되지 않습니다.\n"
                "컨트롤러를 종료한 후 다시 출력해 주세요."
            )
            return True
        return False

    def export_slides_for_overlay(self):
        """
        Export the current session into overlay-ready JSON and launch the controller.

        Steps:

        1) Collect slide session data from the table.
        2) Prepend a blank slide to ensure a clean initial screen.
        3) Convert slides into overlay format via :class:`core.generator.utils.slide_exporter.SlideExporter`.
        4) Write the exported JSON to :py:data:`core.config.paths.SLIDE_FILE` (UTF-8).
        5) Launch the slide controller if it is not already running.

        Args:
            None

        Returns:
            None
        """
        slides = self.data_manager.collect_slide_data()

        # Insert a blank slide as the initial screen
        slides.insert(0, {
            "style": "blank",
            "caption": "",
            "headline": ""
        })

        exporter = SlideExporter(settings={"max_chars": 60})
        exported = exporter.export(slides)

        with open(paths.SLIDE_FILE, "w", encoding="utf-8") as f:
            json.dump(exported, f, ensure_ascii=False, indent=2)

        self.slide_controller_launcher.launch_if_needed(parent_widget=self)

    def handle_table_double_click(self, row: int, column: int):
        """
        Open the style-specific slide editor dialog for the selected table row.

        This method:

        - Reads the current style/caption/headline values from the table row
        - Converts the displayed style label into an internal style key
        - Opens :class:`core.generator.ui.slide_generator_dialog.SlideGeneratorDialog` as a modal editor
        - If the user accepts, writes the updated values back into the table and triggers a save flow

        Args:
            row (int):
                Row index of the double-clicked table row.
            column (int):
                Column index of the double-click event. (Currently unused.)

        Returns:
            None
        """
        from core.generator.ui.slide_generator_dialog import SlideGeneratorDialog

        # Retrieve style key from style alias
        style_combo = self.table.cellWidget(row, 0)
        style_text = style_combo.currentText() if style_combo else "가사"
        style_key = self.reverse_style_aliases.get(style_text, "lyrics")

        # Retrieve current caption and headline
        caption = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        headline = self.table.item(row, 2).text() if self.table.item(row, 2) else ""

        # Launch modal editor dialog
        dialog = SlideGeneratorDialog(style=style_key, caption=caption, headline=headline, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_result()

            # Merge choir name for anthem slides
            new_caption = (
                f"{result.get('caption', '')} {result.get('caption_choir', '')}".strip()
                if result.get("style") == "anthem" else result.get("caption", "")
            )

            # Update table cells
            self.table.setItem(row, 1, QTableWidgetItem(new_caption))
            self.table.setItem(row, 2, QTableWidgetItem(result.get("headline", "")))
            self.handle_ctrl_s()

    def open_settings_dialog(self):
        """
        Open the generator settings dialog and apply changes if accepted.

        If the dialog is accepted:

        - Settings are persisted via the dialog's save routine
        - Font settings are (intended to be) applied to the generator UI

        Args:
            None

        Returns:
            None
        """
        dialog = SettingsDialog(self)
        if dialog.exec():
            settings = dialog.save_settings()
            self.apply_generator_font_settings()

    def apply_generator_font_settings(self):
        """
        Apply the current persistent font settings to the generator UI.

        Reads the generator settings and constructs a `QFont` using:

        - ``font_family`` (default: "Malgun Gothic")
        - ``font_size``   (default: 24)
        - ``font_weight`` (default: "Normal"; "Bold" enables bold)

        Args:
            None

        Returns:
            None
        """
        settings = load_generator_settings()
        family = settings.get("font_family", "Malgun Gothic")
        size = settings.get("font_size", 24)
        weight = settings.get("font_weight", "Normal")

        font = QFont(family, size)
        font.setBold(weight == "Bold")