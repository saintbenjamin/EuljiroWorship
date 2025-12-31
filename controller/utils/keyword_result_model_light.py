# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/controller/utils/keyword_result_model_light.py

Lightweight QAbstractTableModel for displaying Bible keyword search results.

This module defines a minimal table model optimized for keyword search output:
- Two-column layout: Bible reference and verse text
- Designed for read-only display in QTableView
- Supports tooltip display of highlighted (HTML-formatted) verse text
- Uses standard book name mapping for localized display

The model is intentionally lightweight and stateless, suitable for frequent
replacement when running new keyword searches.

Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
Telephone: +82-2-2266-3070
E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
Copyright (c) 2025 The Eulji-ro Presbyterian Church.
License: MIT License with Attribution Requirement (see LICENSE file for details)
"""

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
import json
import os
from core.config import paths

class KeywordResultTableModelLight(QAbstractTableModel):
    """
    Lightweight table model for Bible keyword search results.

    This model presents search results in exactly two columns:
    - Column 0: Bible reference (localized book name + chapter:verse)
    - Column 1: Verse text

    Design notes:
    - Read-only model (no editing or mutation support)
    - Optimized for rapid recreation on each search
    - Tooltip role is used to expose highlighted (HTML) text for delegates

    Attributes:
        results (list[dict]):
            List of search result dictionaries.
            Each entry is expected to contain:
                - 'book'
                - 'chapter'
                - 'verse'
                - 'text'
                - optional 'highlighted'
        book_names (dict[str, str]):
            Mapping from internal book IDs to localized (Korean) book names.
    """

    def __init__(self, results):
        """
        Initialize the model with keyword search results.

        Args:
            results (list[dict]):
                List of search result entries.
                Each dictionary should include at least:
                    - book
                    - chapter
                    - verse
                    - text
                An optional 'highlighted' field may be provided for tooltip display.

        Returns:
            None
        """
        super().__init__()
        self.results = results
        self.book_names = self.load_book_names()

    def load_book_names(self):
        """
        Load localized Bible book names from the standard book definition file.

        Reads the JSON file defined by paths.STANDARD_BOOK_FILE and extracts
        Korean book names for display in the reference column.

        Returns:
            dict[str, str]:
                Mapping from internal book ID to Korean book name.
                Returns an empty dictionary if loading fails.
        """
        path = os.path.join(paths.STANDARD_BOOK_FILE)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: v.get("ko", k) for k, v in data.items()}
        except Exception:
            return {}

    def rowCount(self, parent=QModelIndex()):
        """
        Return the number of rows in the model.

        Args:
            parent (QModelIndex):
                Unused parent index (required by Qt interface).

        Returns:
            int:
                Number of search result entries.
        """
        return len(self.results)

    def columnCount(self, parent=QModelIndex()):
        """
        Return the number of columns in the model.

        This model always exposes exactly two columns:
        - Reference
        - Verse text

        Args:
            parent (QModelIndex):
                Unused parent index (required by Qt interface).

        Returns:
            int:
                Number of columns (always 2).
        """
        return 2

    def data(self, index, role=Qt.DisplayRole):
        """
        Return data for the given index and role.

        Supported roles:
        - Qt.DisplayRole:
            - Column 0: Formatted Bible reference (book chapter:verse)
            - Column 1: Verse text
        - Qt.ToolTipRole:
            - Column 1: Highlighted HTML text if available, otherwise plain text

        Args:
            index (QModelIndex):
                Model index identifying row and column.
            role (Qt.ItemDataRole):
                Requested data role.

        Returns:
            str | None:
                Data for the given role, or None if not applicable.
        """
        if not index.isValid():
            return None

        row, col = index.row(), index.column()
        result = self.results[row]

        if role == Qt.DisplayRole:
            if col == 0:
                book_id = result["book"]
                book_name = self.book_names.get(book_id, book_id)
                return f"{book_name} {result['chapter']}:{result['verse']}"
            elif col == 1:
                return result["text"]

        elif role == Qt.ToolTipRole and col == 1:
            return result.get("highlighted", result["text"])

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Return header labels for the table view.

        Provides Korean column headers for horizontal orientation.

        Args:
            section (int):
                Column index.
            orientation (Qt.Orientation):
                Header orientation (horizontal or vertical).
            role (Qt.ItemDataRole):
                Requested data role.

        Returns:
            str | None:
                Column header label if applicable, otherwise None.
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return ["성경구절", "본문"][section]
        return None