# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/ui/slide_table_manager.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Row-level table operations for the slide generator.

This module defines `SlideTableManager`, a helper class responsible for
manipulating rows in the slide table widget used by the generator UI.
It encapsulates all row operations (insert, delete, move, swap) and
coordinates with the parent generator to enforce edit restrictions
(e.g., when the slide controller is running).
"""

from PySide6.QtWidgets import QComboBox, QTableWidgetItem
from core.config.style_map import STYLE_LIST

class SlideTableManager:
    """
    Manage row-level operations on the slide table.

    This class owns all logic related to modifying the table rows that
    represent slides, including insertion, deletion, reordering, and
    style selection handling. It delegates edit-safety checks to the
    parent generator to ensure consistency with the controller state.

    Attributes
    ----------
    table : QTableWidget
        The table widget that lists slide rows.
    generator :
        Reference to the main slide generator window, used for edit
        permission checks and coordination.
    """

    def __init__(self, table, generator):
        """
        Initialize the table manager.

        Args:
            table (QTableWidget):
                The table widget used to display and edit slide rows.
            generator:
                The main SlideGenerator window. This object is queried to
                determine whether edits are currently allowed.
        """
        self.table = table
        self.generator = generator

    def add_row(self):
        """
        Append a new slide row to the end of the table.

        If the slide controller is currently running, the operation is
        aborted to prevent edits that would not be reflected in output.

        Args:
            None

        Returns:
            None
        """
        if self.generator.warn_if_controller_running():
            return
        self.insert_row(self.table.rowCount())

    def insert_row(self, row=None, above=True, connect_signal=True):
        """
        Insert a new slide row at a specified position.

        If no explicit row index is provided, the insertion position is
        determined from the current table selection. A style selection
        combo box and empty caption/headline cells are created for the row.

        Args:
            row (int | None):
                Target row index. If None, uses the current selection or
                appends to the end of the table.
            above (bool):
                If True, insert above the reference row; otherwise insert below.
            connect_signal (bool):
                Whether to connect the style combo box change signal to
                the corresponding handler.

        Returns:
            None
        """
        if self.generator.warn_if_controller_running():
            return

        # Determine insertion index
        if row is None:
            current_row = self.table.currentRow()
            row = self.table.rowCount() if current_row == -1 else (current_row if above else current_row + 1)
        else:
            row = row if above else row + 1

        self.table.insertRow(row)

        # Style combo box
        combo = QComboBox()
        combo.addItems(STYLE_LIST)
        combo.setMinimumWidth(20)

        if connect_signal:
            combo.setProperty("row_index", row)
            combo.currentIndexChanged.connect(lambda _, r=row: self.handle_combo_change_by_row(r))

        # Add cells to row
        self.table.setCellWidget(row, 0, combo)
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.setItem(row, 2, QTableWidgetItem(""))

        # Focus the new row
        self.table.setCurrentCell(row, 0)

    def handle_combo_change_by_row(self, row):
        """
        Handle a style change in the combo box for a specific row.

        This method is triggered when the style combo box in the given row
        changes. It is intended to synchronize the selected style with
        other parts of the generator UI (e.g., the right-hand detail pane).

        Args:
            row (int):
                Row index whose style selection has changed.

        Returns:
            None
        """
        combo = self.table.cellWidget(row, 0)
        if combo is None:
            print(f"[!] No combo found in row {row}")
            return

    def delete_selected_row(self):
        """
        Delete the currently selected slide row from the table.

        If no row is selected, this method does nothing. If the slide
        controller is running, deletion is aborted.

        Args:
            None

        Returns:
            None
        """
        if self.generator.warn_if_controller_running():
            return
        selected = self.table.currentRow()
        if selected >= 0:
            self.table.removeRow(selected)

    def move_row_up(self):
        """
        Move the selected slide row up by one position.

        If the selected row is already at the top, no action is taken.

        Args:
            None

        Returns:
            None
        """
        row = self.table.currentRow()
        if row > 0:
            self.swap_rows(row, row - 1)
            self.table.selectRow(row - 1)

    def move_row_down(self):
        """
        Move the selected slide row down by one position.

        If the selected row is already at the bottom, no action is taken.

        Args:
            None

        Returns:
            None
        """
        row = self.table.currentRow()
        if row < self.table.rowCount() - 1:
            self.swap_rows(row, row + 1)
            self.table.selectRow(row + 1)

    def swap_rows(self, row1, row2):
        """
        Swap the contents of two rows in the slide table.

        This includes swapping:
        - The selected values of the style combo boxes
        - The text contents of the caption and headline cells

        Args:
            row1 (int):
                Index of the first row.
            row2 (int):
                Index of the second row.

        Returns:
            None

        Raises:
            IndexError:
                If either row index is out of bounds for the table.
        """
        for col in range(3):
            if col == 0:
                # Swap combo box selections
                w1 = self.table.cellWidget(row1, col)
                w2 = self.table.cellWidget(row2, col)
                if w1 and w2:
                    t1 = w1.currentText()
                    t2 = w2.currentText()
                    w1.setCurrentText(t2)
                    w2.setCurrentText(t1)
            else:
                # Swap cell text
                item1 = self.table.item(row1, col)
                item2 = self.table.item(row2, col)
                t1 = item1.text() if item1 else ""
                t2 = item2.text() if item2 else ""
                self.table.setItem(row1, col, QTableWidgetItem(t2))
                self.table.setItem(row2, col, QTableWidgetItem(t1))