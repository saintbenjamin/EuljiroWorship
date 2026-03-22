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
import shutil
import re

from PySide6.QtWidgets import (
    QMainWindow, QTableWidget, QWidget,
    QFileDialog, QMessageBox, QHeaderView,
    QAbstractItemView, QInputDialog, QDialog,
    QTableWidgetItem, QDialogButtonBox,
    QVBoxLayout, QFormLayout, QLineEdit
)
from PySide6.QtGui import QFont

from core.config import paths, style_map, constants
from core.generator.settings_generator import load_generator_settings
from core.generator.settings_last_path import load_last_path, save_last_path
from core.generator.ui.settings_dialog import SettingsDialog
from core.generator.ui.slide_generator_ui_builder import SlideGeneratorUIBuilder
from core.generator.ui.slide_table_manager import SlideTableManager
from core.generator.utils.slide_exporter import SlideExporter
from core.generator.utils.slide_generator_data_manager import SlideGeneratorDataManager
from core.generator.utils.hwpx_announcement_parser import extract_announcement_slides_from_hwpx
from core.plugin.slide_controller_launcher import SlideControllerLauncher
from core.generator.utils.hwpx_worship_order_parser import extract_first_service_order_entries_from_hwpx
from core.utils.bible_parser import parse_reference
from core.utils.bible_data_loader import BibleDataLoader

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
        load_path = self.prompt_load_from_file()  # Shows OS file dialog on startup
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

    def _get_default_load_directory(self) -> str:
        """
        Return the initial directory used by the slide file open dialog.

        Returns:
            str:
                Directory path derived from the last opened/saved slide file,
                or the current working directory if no usable record exists.
        """
        last_path = load_last_path()
        if last_path and os.path.isfile(last_path):
            return os.path.dirname(last_path)
        return os.getcwd()

    def _prompt_worship_title(self, default_title: str) -> str | None:
        """
        Ask the user for the worship title that should back the session filename.

        The dialog is pre-filled with the selected JSON filename stem. Empty
        values and filenames containing invalid characters are rejected and the
        user is prompted again until a valid value is entered.

        If the user presses Cancel or closes the dialog, the original default
        title is used instead of aborting the load flow.

        Args:
            default_title (str):
                Initial text shown in the input field.

        Returns:
            str | None:
                Validated title text.
        """
        invalid_chars = '<>:"/\\\\|?*'
        current_default = default_title

        while True:
            dialog = QInputDialog(self)
            dialog.setWindowTitle("예배 제목을 입력하세요.")
            dialog.setLabelText("예배 제목")
            dialog.setInputMode(QInputDialog.TextInput)
            dialog.setTextValue(current_default)

            # dialog.setMinimumWidth(640)
            dialog.resize(640, dialog.sizeHint().height())

            if dialog.exec() != QDialog.DialogCode.Accepted:
                title = default_title
            else:
                title = dialog.textValue()

            title = title.strip()
            if title.lower().endswith(".json"):
                title = title[:-5].strip()

            if not title:
                QMessageBox.warning(self, "입력 오류", "예배 제목은 비워둘 수 없습니다.")
                continue

            if any(ch in invalid_chars for ch in title):
                QMessageBox.warning(
                    self,
                    "입력 오류",
                    "파일명에 사용할 수 없는 문자가 포함되어 있습니다."
                )
                current_default = title
                continue

            return title

    def _resolve_selected_session_path(self, source_path: str) -> str | None:
        """
        Resolve the actual path to load after a user picks a session JSON file.

        Keeping the default title loads the original file. Changing the title
        creates a same-folder copy with the new filename and loads that copy.

        Args:
            source_path (str):
                Path selected in the open-file dialog.

        Returns:
            str | None:
                Path that should be loaded into the generator, or ``None`` if
                the title step is canceled or the copy operation fails.
        """
        source_dir = os.path.dirname(source_path)
        source_stem, source_ext = os.path.splitext(os.path.basename(source_path))
        source_ext = source_ext or ".json"
        default_title = source_stem

        while True:
            requested_title = self._prompt_worship_title(default_title)
            if requested_title is None:
                return None

            if requested_title == source_stem:
                return source_path

            target_path = os.path.join(source_dir, f"{requested_title}{source_ext}")
            if os.path.abspath(target_path) == os.path.abspath(source_path):
                return source_path

            if os.path.exists(target_path):
                overwrite = QMessageBox.question(
                    self,
                    "같은 이름의 파일이 있습니다.",
                    f"이미 같은 이름의 파일이 있습니다.\n\n{target_path}\n\n기존 파일을 덮어쓸까요?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if overwrite != QMessageBox.StandardButton.Yes:
                    default_title = requested_title
                    continue

            try:
                shutil.copy2(source_path, target_path)
            except Exception as exc:
                QMessageBox.critical(
                    self,
                    "복제 실패",
                    f"선택한 예배 파일을 새 이름으로 복제하지 못했습니다.\n{exc}"
                )
                return None

            return target_path

    def prompt_load_from_file(self):
        """
        Interactively select a slide JSON file and load it into the generator.

        This wrapper owns the startup/manual-open flow that the user sees:

        1. Show the OS file-open dialog.
        2. Ask for the worship title using the filename stem as the default.
        3. If the title changes, duplicate the JSON file in the same folder.
        4. Load the chosen original/copy into the generator.

        Returns:
            str | None:
                Loaded file path, or ``None`` if the flow is canceled.
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "遺덈윭???뚯씪 ?좏깮",
            self._get_default_load_directory(),
            "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return None

        path = self._resolve_selected_session_path(path)
        if not path:
            return None

        return self.load_from_file(path)

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
        self.last_saved_path = path
        self.first_save_done = False
        save_last_path(path)
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
        save_last_path(path)

    def _get_announcement_import_settings_path(self) -> str:
        """
        Return the JSON path used to persist announcement import range settings.

        This file is stored alongside the existing "last opened file" setting
        so that the announcement import feature can keep its own lightweight,
        dedicated configuration without affecting unrelated generator settings.

        Args:
            None

        Returns:
            str:
                Absolute path to the announcement import settings JSON file.
        """
        settings_dir = os.path.dirname(paths.SETTING_LAST_OPEN_FILE)
        return os.path.join(settings_dir, "announcement_import_settings.json")

    def _load_announcement_import_settings(self) -> dict:
        """
        Load persisted announcement import marker settings.

        If the settings file does not exist or cannot be parsed, default marker
        values are returned.

        Args:
            None

        Returns:
            dict:
                Dictionary containing:

                - ``start_headline`` (str):
                    Headline text that marks the first slide of the import block.
                - ``end_headline`` (str):
                    Headline text that marks the last slide of the import block.
                    If empty, the block extends to the end of the file.
        """
        default_settings = {
            "start_headline": "오늘 처음 오신 분들을 환영하고 축복합니다!",
            "end_headline": ""
        }

        settings_path = self._get_announcement_import_settings_path()
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                default_settings.update({
                    "start_headline": loaded.get("start_headline", default_settings["start_headline"]),
                    "end_headline": loaded.get("end_headline", default_settings["end_headline"]),
                })
        except Exception:
            pass

        return default_settings

    def _save_announcement_import_settings(self, start_headline: str, end_headline: str) -> None:
        """
        Save announcement import marker settings to a dedicated JSON file.

        Args:
            start_headline (str):
                Headline text marking the first slide of the import block.
            end_headline (str):
                Headline text marking the last slide of the import block.
                If empty, the block extends to the end of the file.

        Returns:
            None
        """
        settings_path = self._get_announcement_import_settings_path()
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)

        data = {
            "start_headline": start_headline,
            "end_headline": end_headline,
        }

        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _prompt_announcement_import_range(
        self,
        start_default: str,
        end_default: str
    ) -> tuple[str | None, str | None]:
        """
        Open a modal dialog that asks the user for announcement import markers.

        The dialog lets the user define the start and end headlines used when
        extracting and replacing the announcement block. If the end headline is
        left empty, the import block extends to the end of the file.

        Args:
            start_default (str):
                Default text to pre-fill in the start marker field.
            end_default (str):
                Default text to pre-fill in the end marker field.

        Returns:
            tuple[str | None, str | None]:
                Two-element tuple of ``(start_headline, end_headline)``.

                - If the user accepts the dialog, stripped string values are returned.
                - If the user cancels the dialog, ``(None, None)`` is returned.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("광고 가져오기 범위 설정")
        dialog.setMinimumWidth(520)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        start_input = QLineEdit(start_default)
        end_input = QLineEdit(end_default)

        start_input.setPlaceholderText("가져오기 시작 headline")
        end_input.setPlaceholderText("가져오기 끝 headline (비우면 파일 끝까지)")

        form.addRow("가져오기 시작", start_input)
        form.addRow("가져오기 끝", end_input)
        layout.addLayout(form)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None, None

        return start_input.text().strip(), end_input.text().strip()

    def _find_slide_index_by_headline(
        self,
        slides: list[dict],
        headline: str,
        start_index: int = 0
    ) -> int | None:
        """
        Find the first slide index whose headline matches the given text.

        Matching is performed using stripped exact string comparison.

        Args:
            slides (list[dict]):
                Slide dictionaries to search.
            headline (str):
                Target headline text to match.
            start_index (int):
                Row index from which to begin the search.

        Returns:
            int | None:
                Index of the first matching slide, or ``None`` if not found.
        """
        target = headline.strip()
        for i in range(start_index, len(slides)):
            if str(slides[i].get("headline", "")).strip() == target:
                return i
        return None

    def _load_slide_list_into_table(self, slides: list[dict]) -> None:
        """
        Load an in-memory slide list into the generator table.

        This helper clears the current table contents, recreates the required
        rows, and writes each slide's style/caption/headline into the visible UI.

        Args:
            slides (list[dict]):
                Slide dictionaries to render into the generator table.

        Returns:
            None
        """
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for _ in slides:
            self.data_manager._insert_empty_row()

        for row, slide in enumerate(slides):
            combo = self.table.cellWidget(row, 0)
            if combo:
                combo.blockSignals(True)
                combo.setCurrentText(
                    style_map.STYLE_ALIASES.get(slide.get("style", "lyrics"), "찬양가사")
                )
                combo.blockSignals(False)

            style = slide.get("style", "lyrics")
            caption = slide.get("caption", "")
            headline = slide.get("headline", "")

            if style == "anthem":
                caption = f"{slide.get('caption', '')} {slide.get('caption_choir', '')}".strip()

            if style == "verse":
                headline = self.data_manager._split_verse_headline(headline)

            self.table.setItem(row, 1, QTableWidgetItem(caption))
            self.table.setItem(row, 2, QTableWidgetItem(headline))

        self.table.blockSignals(False)

    def _compact_order_text(self, text: str) -> str:
        """
        Remove whitespace from a worship-order string for loose comparisons.

        Args:
            text (str):
                Source text to normalize for structural matching.

        Returns:
            str:
                Text with all whitespace removed.
        """
        return re.sub(r"\s+", "", str(text or ""))

    def _split_choir_caption_parts(self, choir_name: str) -> tuple[str, str]:
        """
        Split a choir label like ``시온찬양대`` into ``("시온", "찬양대")``.

        Args:
            choir_name (str):
                Full choir label parsed from the worship-order source.

        Returns:
            tuple[str, str]:
                Two-element tuple of ``(caption, caption_choir)``.
            If no standard suffix is found, returns ``(choir_name, "")``.
        """
        choir_name = str(choir_name or "").strip()
        if not choir_name:
            return "", ""

        suffix = "찬양대"
        if choir_name.endswith(suffix):
            main = choir_name[:-len(suffix)].strip()
            return main or choir_name, suffix if main else ""

        return choir_name, ""

    def _get_default_bible_version_for_order_import(self) -> str:
        """
        Choose the preferred Bible version for worship-order verse imports.

        The selection prioritizes locally available Korean Revised Version
        files and falls back to the first available JSON Bible dataset when the
        preferred names are not present.

        Args:
            None

        Returns:
            str:
                Version name to pass to ``BibleDataLoader``.
        """
        preferred_candidates = [
            "대한민국 개역개정 (1998)",
            "대한민국 개역개정 (1998) copy",
        ]

        available_versions = [
            filename[:-5]
            for filename in os.listdir(paths.BIBLE_DATA_DIR)
            if filename.endswith(".json")
        ]

        for candidate in preferred_candidates:
            if candidate in available_versions:
                return candidate

        for version in available_versions:
            if version.startswith("대한민국 ") and "개역개정" in version:
                return version

        for version in available_versions:
            if "개역개정" in version:
                return version

        for version in available_versions:
            if version.startswith("대한민국 "):
                return version

        return sorted(available_versions)[0] if available_versions else preferred_candidates[0]

    def _build_hymn_slide_from_number(self, number: int) -> dict:
        """
        Build a hymn slide payload from a hymn number dataset.

        Args:
            number (int):
                Hymn number to load from ``data/hymns``.

        Returns:
            dict:
                Slide dictionary containing the hymn style, caption, and
                headline text for the requested hymn.
        """
        path = os.path.join("data", "hymns", f"hymn_{int(number):03d}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return {
            "style": "hymn",
            "caption": data.get("title", f"새찬송가 {number}장"),
            "headline": data.get("headline", ""),
        }

    def _build_respo_slide_from_number(self, number: int) -> dict:
        """
        Build a responsive-reading slide payload from a reading number dataset.

        Args:
            number (int):
                Responsive reading number to load from ``data/respo``.

        Returns:
            dict:
                Slide dictionary containing the responsive-reading style,
                caption, and combined headline HTML text.
        """
        path = os.path.join("data", "respo", f"responsive_{int(number):03d}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        lines = []
        for row in data.get("slides", []):
            speaker = str(row.get("speaker", "")).strip()
            response = str(row.get("headline", "")).strip()
            if speaker or response:
                lines.append(f"<b>{speaker}:</b> {response}")

        return {
            "style": "respo",
            "caption": data.get("title", f"성시교독 {number}번"),
            "headline": "\n".join(lines),
        }

    def _build_verse_slide_from_reference(self, reference: str) -> dict:
        """
        Build a Bible-reading slide payload from a parsed reference string.

        Args:
            reference (str):
                Scripture reference text extracted from the worship-order
                bulletin.

        Returns:
            dict:
                Slide dictionary containing the verse style, caption, and
                resolved Bible text. If parsing fails, an empty verse headline
                is returned with the original caption preserved.
        """
        parsed = parse_reference(reference)
        if not parsed:
            return {
                "style": "verse",
                "caption": reference,
                "headline": "",
            }

        version = self._get_default_bible_version_for_order_import()
        loader = BibleDataLoader()
        loader.load_version(version)

        book_id, chapter, verses = parsed
        if isinstance(verses, tuple) and verses[1] == -1:
            max_verse = len(loader.get_verses(version)[book_id][str(chapter)])
            verses = list(range(1, max_verse + 1))
        elif isinstance(verses, tuple):
            verses = list(range(verses[0], verses[1] + 1))

        book_name = loader.get_standard_book(book_id, "ko")
        blocks = []

        for verse_num in verses:
            verse_text = loader.get_verse(version, book_id, chapter, verse_num)
            if verse_text:
                blocks.append(f"{book_name} {chapter}:{verse_num}\n{verse_text.strip()}")

        return {
            "style": "verse",
            "caption": reference,
            "headline": "\n\n".join(blocks),
        }

    def _classify_worship_order_slide(self, slides: list[dict], index: int) -> str | None:
        """
        Classify a slide into a worship-order slot category.

        Args:
            slides (list[dict]):
                Full slide list currently being analyzed.
            index (int):
                Index of the slide to classify.

        Returns:
            str | None:
                Normalized worship-order kind such as ``hymn`` or ``sermon``,
                or ``None`` when the slide does not match a managed category.
        """
        slide = slides[index]
        style = slide.get("style", "")
        caption = self._compact_order_text(slide.get("caption", ""))
        headline = self._compact_order_text(slide.get("headline", ""))

        if style == "hymn":
            return "hymn"

        if style == "respo":
            return "respo"

        if style == "verse":
            return "verse"

        if style == "anthem":
            return "anthem"

        if style == "prayer":
            return "prayer"

        if style == "corner":
            if "예배의부름" in headline:
                return "call_to_worship"
            if headline == "화답송":
                return "response_song"
            if headline == "화답송영":
                return "response_doxology"
            if headline == "기원":
                return "invocation"
            if "고백의기도" in headline:
                return "confession_prayer"
            if headline == "봉헌":
                return "offering"
            if headline == "봉헌기도":
                return "offering_prayer"
            if headline == "축도":
                return "benediction"
            if headline == "기도" and "설교자" in caption:
                return "post_sermon_prayer"
            if ("성찬" in caption) or ("성찬" in headline):
                return "communion"

            # Sermon-title slides are usually corner slides whose caption contains
            # the preacher information and whose headline is the sermon title.
            if ("목사" in caption or "설교자" in caption) and headline:
                return "sermon"

        if style == "lyrics":
            if "사도신경" in caption or "사도신경" in headline:
                return "creed"
            if index > 0 and slides[index - 1].get("style") == "anthem":
                return "anthem_lyrics"

        return None

    def _describe_worship_order_slide(self, slide: dict) -> str:
        """
        Produce a short human-readable description of a worship-order slide.

        Args:
            slide (dict):
                Slide dictionary to summarize.

        Returns:
            str:
                Compact text summary used in removal-confirmation prompts.
        """
        style = slide.get("style", "")
        caption = str(slide.get("caption", "")).strip()
        headline = str(slide.get("headline", "")).strip()

        if style == "anthem":
            caption = f"{caption} {slide.get('caption_choir', '')}".strip()

        if caption and headline:
            return f"[{style}] {caption} / {headline}"
        if caption:
            return f"[{style}] {caption}"
        if headline:
            return f"[{style}] {headline}"
        return f"[{style}] (빈 순서)"

    def _prompt_remove_missing_worship_order(self, slide: dict) -> bool:
        """
        Ask the user whether a slide missing from the imported order should be removed.

        Args:
            slide (dict):
                Existing slide dictionary that is not present in the imported
                HWPX worship-order data.

        Returns:
            bool:
                ``True`` if the user approves removal, otherwise ``False``.
        """
        description = self._describe_worship_order_slide(slide)
        result = QMessageBox.question(
            self,
            "예배순서 삭제 확인",
            f"예전 예배에는 아래 순서가 있었지만,\n불러온 HWPX에는 없습니다.\n\n{description}\n\n없앨까요?",
            QMessageBox.Ok | QMessageBox.Cancel,
            QMessageBox.Ok,
        )
        return result == QMessageBox.Ok

    def _remove_worship_order_block(self, slides: list[dict], index: int) -> None:
        """
        Remove a managed worship-order block from the working slide list.

        Anthem blocks span two slides in this project: the ``anthem`` slide and
        its following lyrics slide. Other kinds are removed as a single slide.

        Args:
            slides (list[dict]):
                Mutable slide list being updated.
            index (int):
                Index of the first slide in the block to remove.

        Returns:
            None
        """
        if index >= len(slides):
            return

        if slides[index].get("style") == "anthem":
            del slides[index]
            if index < len(slides) and slides[index].get("style") == "lyrics":
                del slides[index]
            return

        del slides[index]

    def _find_communion_insert_index(self, slides: list[dict]) -> int:
        """
        Determine where a communion block should be inserted in the slide list.

        Args:
            slides (list[dict]):
                Working slide list after other worship-order updates.

        Returns:
            int:
                Insertion index for the communion block, typically after the
                last hymn if one exists.
        """
        hymn_indices = [
            idx for idx in range(len(slides))
            if self._classify_worship_order_slide(slides, idx) == "hymn"
        ]
        if hymn_indices:
            return hymn_indices[-1]
        return len(slides)

    def _build_special_worship_order_block(self, kind: str) -> list[dict]:
        """
        Build predefined slide blocks for special worship-order items.

        Args:
            kind (str):
                Special worship-order kind to generate, such as ``communion``.

        Returns:
            list[dict]:
                New slide dictionaries representing the requested special block.
                Returns an empty list when no template is defined.
        """
        templates = {
            "communion": [
                {
                    "style": "corner",
                    "caption": "성찬식",
                    "headline": "성찬",
                }
            ]
        }
        return [dict(row) for row in templates.get(kind, [])]

    def _apply_worship_order_entries(
        self,
        current_slides: list[dict],
        order_entries: list[dict]
    ) -> list[dict]:
        """
        Apply imported worship-order entries to the current generator session.

        This routine updates matching managed slide slots, prompts about
        removing obsolete items, and inserts selected special-order templates
        when needed. Sermon titles are updated conservatively so that imported
        text is preserved unless an exact preacher suffix can be removed using
        the current sermon slide caption as context.

        Args:
            current_slides (list[dict]):
                Existing slide dictionaries collected from the generator table.
            order_entries (list[dict]):
                Parsed worship-order entry dictionaries extracted from HWPX.

        Returns:
            list[dict]:
                Updated slide list ready to be reloaded into the generator
                table.
        """
        slides = [dict(slide) for slide in current_slides]

        kind_indices: dict[str, list[int]] = {}
        for idx in range(len(slides)):
            kind = self._classify_worship_order_slide(slides, idx)
            if kind and kind != "anthem_lyrics":
                kind_indices.setdefault(kind, []).append(idx)

        consumed_counts: dict[str, int] = {}
        parsed_counts: dict[str, int] = {}

        for entry in order_entries:
            kind = entry["kind"]
            parsed_counts[kind] = parsed_counts.get(kind, 0) + 1

            if kind == "communion":
                continue

            current_list = kind_indices.get(kind, [])
            cursor = consumed_counts.get(kind, 0)
            if cursor >= len(current_list):
                continue

            idx = current_list[cursor]
            consumed_counts[kind] = cursor + 1

            if kind == "hymn":
                slides[idx] = self._build_hymn_slide_from_number(entry["number"])

            elif kind == "respo":
                slides[idx] = self._build_respo_slide_from_number(entry["number"])

            elif kind == "verse":
                slides[idx] = self._build_verse_slide_from_reference(entry["reference"])

            elif kind == "anthem":
                parsed_choir_name = str(entry.get("choir", "")).strip()

                choir_caption = slides[idx].get("caption", "")
                choir_suffix = slides[idx].get("caption_choir", "")

                if parsed_choir_name:
                    parsed_caption, parsed_suffix = self._split_choir_caption_parts(parsed_choir_name)
                    if parsed_caption:
                        choir_caption = parsed_caption
                    if parsed_suffix:
                        choir_suffix = parsed_suffix

                slides[idx]["caption"] = choir_caption
                slides[idx]["caption_choir"] = choir_suffix
                slides[idx]["headline"] = entry["title"]

                if idx + 1 < len(slides) and slides[idx + 1].get("style") == "lyrics":
                    slides[idx + 1]["caption"] = entry["title"]

            elif kind == "sermon":
                imported_title = str(entry.get("title", "")).strip()
                current_caption = str(slides[idx].get("caption", "")).strip()

                # If the current sermon slide already contains preacher info in
                # its caption, strip only that exact preacher suffix from the
                # imported HWPX payload. This avoids sacrificing any sermon-title
                # text while still removing duplicated preacher names when the
                # HWPX line is glued together.
                preacher_suffix = ""
                preacher_match = re.search(
                    r"([가-힣A-Za-z·]{2,4}\s*목사)\s*$",
                    current_caption,
                )
                if preacher_match:
                    preacher_suffix = preacher_match.group(1).strip()

                if preacher_suffix:
                    compact_suffix = re.sub(r"\s+", "", preacher_suffix)
                    suffix_pattern = r"\s*".join(re.escape(ch) for ch in compact_suffix)
                    imported_title = re.sub(
                        rf"{suffix_pattern}\s*$",
                        "",
                        imported_title,
                    ).strip()

                slides[idx]["headline"] = imported_title

            elif kind == "prayer":
                slides[idx]["headline"] = entry.get("leader", "")

            elif kind == "post_sermon_prayer":
                slides[idx]["caption"] = "설교자"
                slides[idx]["headline"] = "기도"

            # Fixed liturgy items are only presence-checked for now.

        remove_candidates: list[tuple[int, str]] = []
        managed_kinds = {
            "call_to_worship",
            "response_song",
            "invocation",
            "creed",
            "confession_prayer",
            "respo",
            "prayer",
            "hymn",
            "verse",
            "anthem",
            "sermon",
            "post_sermon_prayer",
            "offering",
            "offering_prayer",
            "benediction",
            "response_doxology",
            "communion",
        }

        for kind, idx_list in kind_indices.items():
            if kind not in managed_kinds:
                continue

            keep_count = parsed_counts.get(kind, 0)
            for idx in idx_list[keep_count:]:
                remove_candidates.append((idx, kind))

        approved_remove_indices: list[tuple[int, str]] = []
        for idx, kind in sorted(remove_candidates, key=lambda item: item[0]):
            if idx >= len(slides):
                continue
            if self._classify_worship_order_slide(slides, idx) != kind:
                continue
            if self._prompt_remove_missing_worship_order(slides[idx]):
                approved_remove_indices.append((idx, kind))

        for idx, kind in sorted(approved_remove_indices, key=lambda item: item[0], reverse=True):
            if idx >= len(slides):
                continue
            if self._classify_worship_order_slide(slides, idx) != kind:
                continue
            self._remove_worship_order_block(slides, idx)

        if parsed_counts.get("communion", 0) > 0 and not kind_indices.get("communion"):
            insert_at = self._find_communion_insert_index(slides)
            slides[insert_at:insert_at] = self._build_special_worship_order_block("communion")

        return slides

    def import_worship_order_from_hwpx(self):
        """
        Import first-service worship-order information from a HWPX bulletin and
        conservatively update matching slots in the current generator session.

        This first-pass implementation updates the existing session structure
        rather than rebuilding the whole file from scratch.

        Args:
            None

        Returns:
            None
        """
        src_path, _ = QFileDialog.getOpenFileName(
            self,
            "예배순서를 가져올 HWPX 주보 파일 선택",
            "",
            "HWPX Files (*.hwpx)"
        )
        if not src_path:
            return

        try:
            order_entries = extract_first_service_order_entries_from_hwpx(src_path)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"HWPX에서 예배순서를 추출하지 못했습니다:\n{e}")
            return

        if not order_entries:
            QMessageBox.warning(self, "실패", "HWPX에서 1부 예배순서를 찾지 못했습니다.")
            return

        current_slides = self.data_manager.collect_slide_data()
        updated_slides = self._apply_worship_order_entries(current_slides, order_entries)

        self._load_slide_list_into_table(updated_slides)

        QMessageBox.information(
            self,
            "완료",
            f"HWPX 예배순서 {len(order_entries)}개 항목을 기준으로 현재 JSON을 갱신했습니다."
        )

    def import_announcements_from_hwpx(self):
        """
        Import announcements from a HWPX bulletin and replace the current
        announcement area between the fixed welcome slide and the fixed
        closing-verse slide.

        Imported items are intentionally inserted as ``lyrics`` style only.

        The source HWPX file is parsed into announcement slides, and the
        matching range in the current session is replaced using fixed headline
        anchors that mark the start and end of the announcement block.

        Args:
            None

        Returns:
            None
        """
        start_anchor = "오늘 처음 오신 분들을 환영하고 축복합니다!"
        end_anchor = "용서, 사랑의 시작입니다"
        wrap_width = 28

        src_path, _ = QFileDialog.getOpenFileName(
            self,
            "광고를 가져올 HWPX 주보 파일 선택",
            "",
            "HWPX Files (*.hwpx)"
        )
        if not src_path:
            return

        try:
            imported_slides = extract_announcement_slides_from_hwpx(
                src_path,
                wrap_width=wrap_width
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"HWPX에서 광고를 추출하지 못했습니다:\n{e}")
            return

        if not imported_slides:
            QMessageBox.warning(self, "실패", "HWPX에서 광고 항목을 찾지 못했습니다.")
            return

        current_slides = self.data_manager.collect_slide_data()

        start_idx = self._find_slide_index_by_headline(current_slides, start_anchor)
        if start_idx is None:
            QMessageBox.warning(
                self,
                "실패",
                f"현재 파일에서 광고 시작 기준 슬라이드를 찾지 못했습니다.\n\n{start_anchor}"
            )
            return

        end_idx = self._find_slide_index_by_headline(
            current_slides,
            end_anchor,
            start_index=start_idx + 1
        )
        if end_idx is None:
            QMessageBox.warning(
                self,
                "실패",
                f"현재 파일에서 광고 끝 기준 슬라이드를 찾지 못했습니다.\n\n{end_anchor}"
            )
            return

        if end_idx <= start_idx:
            QMessageBox.warning(
                self,
                "실패",
                "광고 끝 기준 슬라이드가 시작 기준 슬라이드보다 앞에 있습니다."
            )
            return

        new_slides = (
            current_slides[:start_idx + 1]
            + imported_slides
            + current_slides[end_idx:]
        )

        self._load_slide_list_into_table(new_slides)

        QMessageBox.information(
            self,
            "완료",
            f"HWPX 광고 {len(imported_slides)}개를 가져왔습니다."
        )

    def import_announcements(self):
        """
        Import a configurable slide block from an external slide JSON file and
        replace the corresponding block in the current session.

        This method opens a file-selection dialog, asks the user for the start
        and end headline markers that define the import range, persists those
        marker values to a dedicated settings JSON file, and then replaces the
        matching range in the currently loaded generator table.

        The imported range is extracted from the selected source file and applied
        onto the current session using the same start/end markers.

        Args:
            None

        Returns:
            None

        Raises:
            None explicitly.
            Any file I/O or JSON parsing errors are handled internally and
            reported to the user via message dialogs.

        Notes:
            - Range boundaries are detected by exact headline matching after
            stripping leading and trailing whitespace.
            - If the end marker is empty, the import block extends to the end
            of the file.
            - If either the source file or the current session does not contain
            the requested start marker, no changes are applied.
            - This function modifies the generator table in place and does not
            automatically save the session file.
            - User-edited start/end marker values are persisted and reused as
            defaults in subsequent imports.
        """
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        # ── 1. Select source file ─────────────────────────────
        src_path, _ = QFileDialog.getOpenFileName(
            self,
            "광고를 가져올 예배 파일 선택",
            "",
            "JSON Files (*.json)"
        )
        if not src_path:
            return

        # ── 2. Load persisted defaults and ask for range ─────
        settings = self._load_announcement_import_settings()
        start_default = settings.get("start_headline", "오늘 처음 오신 분들을 환영하고 축복합니다!")
        end_default = settings.get("end_headline", "")

        start_headline, end_headline = self._prompt_announcement_import_range(
            start_default=start_default,
            end_default=end_default
        )
        if start_headline is None:
            return

        if not start_headline:
            QMessageBox.warning(self, "실패", "시작 headline은 비워둘 수 없습니다.")
            return

        self._save_announcement_import_settings(start_headline, end_headline)

        # ── 3. Load source slides ─────────────────────────────
        try:
            with open(src_path, "r", encoding="utf-8") as f:
                src_slides = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일을 읽을 수 없습니다:\n{e}")
            return

        if not isinstance(src_slides, list):
            QMessageBox.warning(self, "실패", "원본 파일 형식이 올바르지 않습니다.")
            return

        # ── 4. Find source range ──────────────────────────────
        start_src = self._find_slide_index_by_headline(src_slides, start_headline)
        if start_src is None:
            QMessageBox.warning(self, "실패", "원본 파일에서 시작 headline을 찾을 수 없습니다.")
            return

        if end_headline:
            end_src = self._find_slide_index_by_headline(src_slides, end_headline, start_index=start_src)
            if end_src is None:
                QMessageBox.warning(self, "실패", "원본 파일에서 끝 headline을 찾을 수 없습니다.")
                return
            if end_src < start_src:
                QMessageBox.warning(self, "실패", "원본 파일에서 끝 headline이 시작 headline보다 앞에 있습니다.")
                return
        else:
            end_src = len(src_slides) - 1

        announcement_block = src_slides[start_src:end_src + 1]

        # ── 5. Collect current slides and find target range ──
        current_slides = self.data_manager.collect_slide_data()

        start_dst = self._find_slide_index_by_headline(current_slides, start_headline)
        if start_dst is None:
            QMessageBox.warning(self, "실패", "현재 파일에서 시작 headline을 찾을 수 없습니다.")
            return

        if end_headline:
            end_dst = self._find_slide_index_by_headline(current_slides, end_headline, start_index=start_dst)
            if end_dst is None:
                QMessageBox.warning(self, "실패", "현재 파일에서 끝 headline을 찾을 수 없습니다.")
                return
            if end_dst < start_dst:
                QMessageBox.warning(self, "실패", "현재 파일에서 끝 headline이 시작 headline보다 앞에 있습니다.")
                return
        else:
            end_dst = len(current_slides) - 1

        new_slides = current_slides[:start_dst] + announcement_block + current_slides[end_dst + 1:]

        # ── 6. Reload table with new slides ───────────────────
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for _ in new_slides:
            self.data_manager._insert_empty_row()

        for row, slide in enumerate(new_slides):
            combo = self.table.cellWidget(row, 0)
            if combo:
                combo.blockSignals(True)
                combo.setCurrentText(
                    style_map.STYLE_ALIASES.get(slide.get("style", "lyrics"), "찬양가사")
                )
                combo.blockSignals(False)

            style = slide.get("style", "lyrics")
            caption = slide.get("caption", "")
            headline = slide.get("headline", "")

            if style == "anthem":
                caption = f"{slide.get('caption', '')} {slide.get('caption_choir', '')}".strip()

            if style == "verse":
                headline = self.data_manager._split_verse_headline(headline)

            self.table.setItem(row, 1, QTableWidgetItem(caption))
            self.table.setItem(row, 2, QTableWidgetItem(headline))

        self.table.blockSignals(False)

        QMessageBox.information(self, "완료", "지정한 범위의 슬라이드를 가져왔습니다.")

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

        See also :py:data:`core.config.constants.MAX_CHARS`.

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

        exporter = SlideExporter(settings={"max_chars": constants.MAX_CHARS})
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
