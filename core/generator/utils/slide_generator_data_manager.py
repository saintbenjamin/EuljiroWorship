# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/generator/utils/slide_generator_data_manager.py

Data management layer for the slide generator table UI.

This module defines SlideGeneratorDataManager, which is responsible for
loading slide data from JSON files into the generator table, collecting
edited table contents back into structured slide dictionaries, and
handling style-specific normalization (e.g., anthem choir names,
Bible verse formatting).

It acts as the sole translation layer between:
- Persistent slide JSON files
- The QTableWidget-based generator UI

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import json
import re
from PySide6.QtWidgets import QTableWidgetItem, QComboBox
from core.utils.bible_data_loader import BibleDataLoader
from core.config import style_map

class SlideGeneratorDataManager:
    """
    Manage slide data exchange between JSON files and the generator table UI.

    Responsibilities:
    - Load slide JSON data into the QTableWidget
    - Convert table rows back into structured slide dictionaries
    - Handle style-specific preprocessing and normalization
      (e.g., anthem choir names, verse formatting)

    This class intentionally contains no UI logic beyond table population,
    serving as a thin data-adapter layer.

    Args:
        table_widget (QTableWidget):
            The table widget used in the slide generator UI.
    """

    def __init__(self, table_widget):
        """
        Initialize the data manager with a reference to the generator table.

        Args:
            table_widget (QTableWidget):
                Table widget that stores slide rows in the generator UI.
        """
        self.table = table_widget
        self.loader = BibleDataLoader()

    def load_from_file(self, path: str) -> list[dict]:
        """
        Load slide data from a JSON file and populate the generator table.

        This method:
        - Clears the existing table
        - Inserts rows matching the number of slides
        - Applies style aliases to the style combo box
        - Performs style-specific preprocessing:
            * Merges anthem caption and choir name
            * Formats multi-verse Bible slides for readability

        Args:
            path (str):
                Path to the slide JSON file.

        Returns:
            list[dict]:
                List of slide dictionaries loaded from the file.
        """
        with open(path, "r", encoding="utf-8") as f:
            slide_data = json.load(f)

        # Temporarily block signals to avoid triggering UI events
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for _ in slide_data:
            self._insert_empty_row()

        for row, slide in enumerate(slide_data):
            combo = self.table.cellWidget(row, 0)
            if combo:
                combo.blockSignals(True)
                combo.setCurrentText(style_map.STYLE_ALIASES.get(slide.get("style", "lyrics"), "찬양가사"))
                combo.blockSignals(False)

            style = slide.get("style", "lyrics")
            caption = slide.get("caption", "")
            headline = slide.get("headline", "")

            # Merge choir name if anthem
            if style == "anthem":
                caption = f"{slide.get('caption', '')} {slide.get('caption_choir', '')}".strip()

            # Pre-process verse lines for readability
            if style == "verse":
                headline = self._split_verse_headline(headline)

            self.table.setItem(row, 1, QTableWidgetItem(caption))
            self.table.setItem(row, 2, QTableWidgetItem(headline))

        self.table.blockSignals(False)
        return slide_data

    def save_to_file(self, path: str) -> None:
        """
        Save the current table contents to a JSON slide file.

        Args:
            path (str):
                Destination file path.
        """
        data = self.collect_slide_data()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def collect_slide_data(self) -> list[dict]:
        """
        Collect slide data from the generator table and normalize it.

        This method reads each table row and converts it into a slide
        dictionary using internal style keys. Style-specific handling
        is applied where necessary (e.g., anthem caption/choir separation).

        Returns:
            list[dict]:
                List of structured slide dictionaries.
        """
        result = []
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 0)
            if not combo:
                continue

            style = style_map.REVERSE_ALIASES.get(combo.currentText(), "lyrics")
            caption = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            headline = self.table.item(row, 2).text() if self.table.item(row, 2) else ""

            if style == "anthem":
                # Separate main title and choir name if possible
                parts = caption.strip().split()
                if len(parts) == 2:
                    result.append({
                        "style": "anthem",
                        "caption": parts[0],
                        "caption_choir": parts[1],
                        "headline": headline
                    })
                else:
                    result.append({
                        "style": "anthem",
                        "caption": caption,
                        "caption_choir": "",
                        "headline": headline
                    })
            else:
                result.append({
                    "style": style,
                    "caption": caption,
                    "headline": headline
                })
        return result

    def _insert_empty_row(self):
        """
        Insert a new empty slide row into the generator table.

        The row includes:
        - A style selection combo box
        - Empty caption and headline cells
        """
        row = self.table.rowCount()
        self.table.insertRow(row)

        combo = QComboBox()
        combo.addItems(style_map.STYLE_ALIASES.values())
        self.table.setCellWidget(row, 0, combo)
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.setItem(row, 2, QTableWidgetItem(""))

    def _split_verse_headline(self, text: str) -> str:
        """
        Reformat concatenated Bible verse text into a readable multi-line form.

        If multiple verse references are detected, this method splits the text
        so that each reference and its verse body are separated by blank lines.
        Single-verse text is returned unchanged.

        Args:
            text (str):
                Raw verse headline string.

        Returns:
            str:
                Reformatted verse text suitable for display in the table.
        """
        book_names = [re.escape(k) for k in self.loader.aliases_book.keys()]
        book_pattern = "|".join(sorted(book_names, key=len, reverse=True))
        # Include optional Bible version in parentheses
        pattern = fr"((?:{book_pattern})\s?\d+장\s?\d+절(?:\s*\([^)]+\))?)"

        if len(re.findall(pattern, text)) >= 2:
            parts = re.split(pattern, text)
            lines = []
            i = 1
            while i < len(parts) - 1:
                ref = parts[i].strip()
                verse_text = parts[i + 1].strip()
                if ref and verse_text:
                    lines.append(f"{ref}\n{verse_text}")
                i += 2
            return "\n\n".join(lines)

        return text