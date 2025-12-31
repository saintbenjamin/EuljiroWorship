# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/controller/slide_controller.py

Main slide controller module for managing and broadcasting slides in real-time.

This module provides the GUI entry point and the main controller widget
used by the slide controller application. It wires together the PySide6 UI,
file watchers, WebSocket broadcasting, and the emergency verse interruptor.

Key responsibilities in this module:
- Ensure the project root is importable (sys.path injection for direct execution)
- Define `launch_interruptor()` to start the verse interruptor as a detached process
- Define `SlideController`, the main QWidget that:
  - loads and displays slide data
  - sends slides via WebSocket
  - reacts to slide file changes / emergency interruptor clear events

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import sys, os

# ─────────────────────────────────────────────
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ─────────────────────────────────────────────
import json
import subprocess
import shutil

# PySide6 GUI essentials
from PySide6.QtWidgets import QApplication, QWidget, QAbstractItemView, QTableWidgetItem
from PySide6.QtCore import Qt, QEvent, QThread, QTimer, Slot

# Project imports
from controller.utils.emergency_caption_handler import EmergencyCaptionHandler
from controller.utils.emergency_slide_factory import EmergencySlideFactory
from controller.utils.interruptor_watcher import InterruptorWatcher
from controller.utils.slide_controller_data_manager import SlideControllerDataManager
from controller.utils.slide_file_watcher import SlideFileWatcher
from controller.ui.slide_controller_ui_builder import SlideControllerUIBuilder
from controller.utils.slide_websocket_manager import SlideWebSocketManager
from core.config import paths
from core.generator.settings_generator import get_font_from_settings

def launch_interruptor():
    """
    Launch the verse interruptor script as a detached background process.

    This starts `launcher/verse_interruptor.py` using the current Python
    interpreter (`sys.executable`) and suppresses stdin/stdout/stderr to
    avoid blocking or cluttering the controller GUI.

    The interruptor script is expected to watch the emergency verse output
    file (e.g., `paths.VERSE_FILE`) and handle its own logic independently.

    Args:
        None

    Returns:
        None
    """
    try:
        with open(os.devnull, "w") as devnull:
            subprocess.Popen(
                [sys.executable, "launcher/verse_interruptor.py"],
                stdout=devnull,
                stderr=devnull,
                stdin=devnull,
                close_fds=True
            )
        print("[✓] Launched verse_interruptor.py")
    except Exception as e:
        print("[x] Failed to launch interruptor:", e)

class SlideController(QWidget):
    """
    Main controller widget for managing and broadcasting worship slides.

    This controller loads slides from a JSON file, displays them in a table UI,
    and broadcasts the currently selected slide to the overlay via WebSocket.
    It also manages "emergency mode" slides and restores the previous slide set
    after the interruptor file is cleared.

    Attributes:
        slide_file (str):
            Path to the slide JSON file.
        ws_uri (str):
            WebSocket URI used to broadcast slide data.
        data (SlideControllerDataManager):
            Slide data manager instance responsible for loading/restoring slides.
        slides (list[dict]):
            Current list of slide dictionaries.
        index (int):
            Current slide index.
        index_backup (int):
            Backup index saved before entering emergency mode.
        emergency_mode (bool):
            Whether the controller is currently in emergency mode.
        slide_factory (EmergencySlideFactory):
            Factory used to build emergency slides.
        ws_manager (SlideWebSocketManager):
            WebSocket manager for overlay communication.
        caption_handler (EmergencyCaptionHandler):
            Dialog/handler used to generate emergency slides from user input.
    """

    def __init__(self, slide_file, ws_uri):
        """
        Initialize the SlideController UI and subsystems.

        This sets up the window, loads slides, connects to the WebSocket server,
        builds the UI, and starts background threads for:
        - Watching slide file changes
        - Watching interruptor (emergency verse) clear events

        Args:
            slide_file (str):
                Path to the slide JSON file to load.
            ws_uri (str):
                WebSocket URI for broadcasting slide data
                (e.g., "ws://127.0.0.1:8765/ws").

        Returns:
            None
        """
        super().__init__()
        self.setWindowTitle("대한예수교장로회(통합) 을지로교회 슬라이드 컨트롤러")
        self.resize(1000, 600)

        # File path and WebSocket info
        self.slide_file = slide_file
        self.ws_uri = ws_uri

        # Load slide data and initial index
        self.data = SlideControllerDataManager(self.slide_file)
        self.data.load_slides()
        self.slides = self.data.slides
        self.index = self.data.index
        self.index_backup = 0

        self.emergency_mode = True
        self.slide_factory = EmergencySlideFactory()

        # WebSocket manager
        self.ws_manager = SlideWebSocketManager(self.ws_uri)
        self.ws_manager.connect()

        # UI setup
        SlideControllerUIBuilder(self).build_ui()

        # Emergency caption handler
        self.caption_handler = EmergencyCaptionHandler(self)
        self.send_current_slide()

        # Set up SlideFileWatcher thread
        self.slide_thread = QThread()
        self.slide_watcher = SlideFileWatcher(self.slide_file)
        self.slide_watcher.moveToThread(self.slide_thread)
        self.slide_watcher.slide_changed.connect(self.on_slide_changed)
        self.slide_watcher.slide_cleared.connect(self.on_slide_cleared)
        self.slide_thread.started.connect(self.slide_watcher.run)
        self.slide_thread.start()

        # Set up InterruptorWatcher thread
        self.interruptor_thread = QThread()
        self.interruptor_watcher = InterruptorWatcher()
        self.interruptor_watcher.moveToThread(self.interruptor_thread)
        self.interruptor_watcher.interruptor_cleared.connect(self.on_interruptor_cleared)
        self.interruptor_thread.started.connect(self.interruptor_watcher.run)
        self.interruptor_thread.start()

        # Apply user font settings (font is set but not directly applied here)
        font = get_font_from_settings()

    def insert_blank_if_needed(self):
        """
        Ensure the slide file begins with a blank slide.

        If the file exists and the first slide is not style "blank", this inserts a
        blank slide at index 0 and writes the updated list back to disk.

        Returns:
            None
        """
        if os.path.exists(paths.SLIDE_FILE):
            try:
                with open(paths.SLIDE_FILE, "r", encoding="utf-8") as f:
                    slides = json.load(f)
                if slides and slides[0].get("style") != "blank":
                    slides.insert(0, {
                        "style": "blank",
                        "caption": "",
                        "headline": ""
                    })
                    with open(paths.SLIDE_FILE, "w", encoding="utf-8") as f:
                        json.dump(slides, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print("[!] Blank insert failed:", e)

    def load_slides(self):
        """
        Load slide data from the controller's slide JSON file.

        Returns:
            list:
                Parsed list of slide dictionaries loaded from disk.
        """
        with open(self.slide_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def keyPressEvent(self, event):
        """
        Handle keyboard navigation for slide movement.

        Right/Down/Space moves forward, Left/Up moves backward.

        Args:
            event (QKeyEvent):
                Key press event object.

        Returns:
            None
        """
        if event.key() in (Qt.Key_Right, Qt.Key_Down, Qt.Key_Space):
            self.next_slide()
        elif event.key() in (Qt.Key_Left, Qt.Key_Up):
            self.prev_slide()

    def update_label(self):
        """
        Update the UI label and table selection for the current slide.

        The label shows:
        - Current page (1-based)
        - Total pages
        - A short preview of the first line of the headline

        Returns:
            None
        """
        slide = self.slides[self.index]
        preview = slide.get("headline", "").split("\n")[0][:80]
        self.label.setText(f"{self.index+1}/{len(self.slides)}: {preview}")
        self.table.selectRow(self.index)

    def send_current_slide(self):
        """
        Send the current slide to the overlay via WebSocket.

        If the WebSocket is connected, the slide dict at `self.index` is sent.
        If not connected, a warning is printed.

        When not in emergency mode, also updates `self.data.index` so the current
        position can be persisted by the data manager.

        Returns:
            None
        """
        slide = self.slides[self.index]

        if self.ws_manager.is_connected():
            self.ws_manager.send(slide)
            # print(f"[→] Sent slide {self.index+1}")
        else:
            print("[!] WebSocket not connected.")

        if not self.emergency_mode:
            self.data.index = self.index

    def next_slide(self):
        """
        Move to the next slide if one exists.

        Increments `self.index`, updates the UI label/table highlight,
        and broadcasts the slide.

        Returns:
            None
        """
        if self.index < len(self.slides) - 1:
            self.index += 1
            self.update_label()
            self.send_current_slide()

    def prev_slide(self):
        """
        Move to the previous slide if available.

        Decrements `self.index`, updates the UI label/table highlight,
        and broadcasts the slide.

        Returns:
            None
        """
        if self.index > 0:
            self.index -= 1
            self.update_label()
            self.send_current_slide()

    def on_cell_clicked(self, row, _column):
        """
        Jump to a slide when a table row is clicked.

        Args:
            row (int):
                The clicked row index (0-based), used as the slide index.
            _column (int):
                Unused column index (Qt signal provides it).

        Returns:
            None
        """
        self.index = row
        self.update_label()
        self.send_current_slide()

    @Slot(list, int)
    def on_slide_changed(self, slides, index):
        """
        Handle slide file modification events from SlideFileWatcher.

        Replaces the internal slide list and index with the new values,
        updates the UI, and broadcasts the current slide.

        Args:
            slides (list):
                Newly loaded slides from the watcher.
            index (int):
                Index to set as the current slide.

        Returns:
            None
        """
        self.slides = slides
        self.index = index
        self.update_label()
        self.send_current_slide()

    @Slot()
    def on_slide_cleared(self):
        """
        Handle slide file cleared events from SlideFileWatcher.

        Attempts to restore slides from backup via the data manager.
        If restoration fails, falls back to a single blank slide.

        Returns:
            None
        """
        print("[!] Slide file was cleared. Attempting to restore...")
        if self.data.restore_from_backup():
            self.slides = self.data.slides
            self.index = self.index_backup
        else:
            self.slides = [{"style": "blank", "caption": "", "headline": ""}]
            self.index = 0
        self.update_label()
        self.send_current_slide()

    @Slot()
    def on_interruptor_cleared(self):
        """
        Handle interruptor-cleared events from InterruptorWatcher.

        When the emergency verse file is cleared, this restores the previous slides
        (via `on_slide_cleared()`) and exits emergency mode.

        Returns:
            None
        """
        print("[✓] Detected interruptor cleared. Restoring previous slides...")
        self.on_slide_cleared()
        self.emergency_mode = False

    def eventFilter(self, source, event):
        """
        Capture key events globally to allow slide navigation without focus.

        This enables arrow/space navigation even when focus is on other widgets.

        Args:
            source (QObject):
                Event source object.
            event (QEvent):
                Incoming event.

        Returns:
            bool:
                True if the event was handled here, otherwise delegates to parent.
        """
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Right, Qt.Key_Down, Qt.Key_Space):
                self.next_slide()
                return True
            elif event.key() in (Qt.Key_Left, Qt.Key_Up):
                self.prev_slide()
                return True
        return super().eventFilter(source, event)

    def launch_emergency_caption(self):
        """
        Enter emergency mode and generate emergency slides from user input.

        Saves the current index to `index_backup`, invokes the emergency caption
        handler, and if slides are returned, replaces the current slide list with
        the emergency slides starting from index 0.

        Returns:
            None
        """
        self.emergency_mode = True
        self.index_backup = self.index
        slides = self.caption_handler.handle()
        if slides:
            self.slides = slides
            self.index = 0
            self.rebuild_table()  # ✅ Update the table
            self.update_label()

    def jump_to_index(self, idx: int):
        """
        Jump directly to a given slide index.

        If the index is valid, sets `self.index`, broadcasts the slide,
        updates the table selection, scrolls it into view, and updates the label.

        Args:
            idx (int):
                Target slide index (0-based).

        Returns:
            None
        """
        if 0 <= idx < len(self.slides):
            self.index = idx
            self.send_current_slide()
            self.table.setCurrentCell(idx, 0)
            self.table.scrollToItem(self.table.item(idx, 0), QAbstractItemView.PositionAtCenter)
            self.update_label()

    def jump_to_previous(self):
        """
        Jump to the previous slide and center it in the table view.

        Returns:
            None
        """
        if self.index > 0:
            self.index -= 1
            self.send_current_slide()
            self.table.setCurrentCell(self.index, 0)
            self.table.scrollToItem(self.table.item(self.index, 0), QAbstractItemView.PositionAtCenter)
            self.update_label()

    def jump_to_next(self):
        """
        Jump to the next slide and center it in the table view.

        Returns:
            None
        """
        if self.index + 1 < len(self.slides):
            self.index += 1
            self.send_current_slide()
            self.table.setCurrentCell(self.index, 0)
            self.table.scrollToItem(self.table.item(self.index, 0), QAbstractItemView.PositionAtCenter)
            self.update_label()

    def jump_to_page(self):
        """
        Jump to a slide page based on the number typed in the page input box.

        The UI value is interpreted as 1-based; internally converted to 0-based.
        If invalid, prints an error message.

        Returns:
            None
        """
        try:
            page_num = int(self.page_input.text()) - 1
            if 0 <= page_num < len(self.slides):
                self.index = page_num
                self.send_current_slide()
                self.table.setCurrentCell(page_num, 0)
                self.table.scrollToItem(self.table.item(page_num, 0), QAbstractItemView.PositionAtCenter)
                self.update_label()
            else:
                print("[!] Invalid page number")
        except ValueError:
            print("[!] Page input is not a valid number")

    def clear_emergency_caption(self):
        """
        Clear the emergency verse output file and restore normal slides.

        This writes an empty string to `paths.VERSE_FILE`, clears `paths.SLIDE_FILE`,
        then attempts restoration from backup via SlideControllerDataManager.

        After restoration, rebuilds the table, updates the label, and scrolls
        the restored index into view.

        Returns:
            None
        """
        with open(paths.VERSE_FILE, "w", encoding="utf-8") as f:
            f.write("")
        with open(paths.SLIDE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)

        slide_manager = SlideControllerDataManager(paths.SLIDE_FILE)
        slide_manager.restore_from_backup()

        self.slides = slide_manager.slides
        self.index = self.index_backup if hasattr(self, "index_backup") else 0
        self.rebuild_table()
        self.update_label()
        QTimer.singleShot(0, lambda: self.table.scrollToItem(
            self.table.item(self.index, 0), QAbstractItemView.PositionAtCenter))

    def rebuild_table(self):
        """
        Rebuild the slide table widget using the current `self.slides`.

        Each row displays:
        - Page number (1-based)
        - Caption
        - First line preview of headline (trimmed)

        Returns:
            None
        """
        self.table.setRowCount(0)
        for i, slide in enumerate(self.slides):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(slide.get("caption", "")))
            headline = slide.get("headline", "").split("\n")[0][:50]
            self.table.setItem(i, 2, QTableWidgetItem(headline))

    def closeEvent(self, event):
        """
        Gracefully stop background threads and disconnect WebSocket before exit.

        Stops file watchers, quits threads, waits for them to finish, disconnects
        the WebSocket manager, then delegates to QWidget.closeEvent().

        Args:
            event (QCloseEvent):
                Close event object.

        Returns:
            None
        """
        self.slide_watcher.stop()
        self.interruptor_watcher.stop()
        self.slide_thread.quit()
        self.interruptor_thread.quit()
        self.slide_thread.wait()
        self.interruptor_thread.wait()
        self.ws_manager.disconnect()
        super().closeEvent(event)

if __name__ == "__main__":
    """
    Entry point for the slide controller application.

    This launches the verse interruptor, applies font settings,
    and starts the GUI event loop.
    """
    SlideControllerDataManager(paths.SLIDE_FILE).backup_slides()

    launch_interruptor()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(get_font_from_settings())

    controller = SlideController(paths.SLIDE_FILE, "ws://127.0.0.1:8765/ws")
    controller.insert_blank_if_needed()
    controller.show()

    sys.exit(app.exec())