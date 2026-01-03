# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/controller/utils/keyword_highlight_delegate.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

QStyledItemDelegate implementation for keyword highlighting in Qt item views.

This module defines a delegate that renders cell text using QTextDocument so that:

- HTML tags (e.g., <b>) are supported.
- Newlines are rendered as multi-line content (<br>).
- Specified keywords are highlighted by wrapping them in red <span> tags.
- Row height can be computed from the HTML-rendered content.

Typical usage::

    view.setItemDelegate(KeywordHighlightDelegate(keywords=["하나님", "세상"]))
"""

from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import QPoint, QSize

class KeywordHighlightDelegate(QStyledItemDelegate):
    """
    Custom item delegate that highlights keywords in model text using HTML rendering.

    This delegate converts the cell text into HTML and wraps each keyword occurrence
    with a red-colored <span>. Rendering is done via QTextDocument to support:
    - HTML formatting
    - Multi-line wrapping
    - Accurate sizeHint calculation

    Args:
        keywords (list[str]):
            Keywords to highlight. Empty strings are ignored.
        parent (QWidget | None):
            Optional parent widget.
    """

    def __init__(self, keywords, parent=None):
        """
        Initialize the delegate with keywords to highlight.

        Args:
            keywords (list[str]):
                Keywords to highlight. Empty strings are ignored.
            parent (QWidget | None):
                Optional parent widget.

        Returns:
            None
        """
        super().__init__(parent)
        self.keywords = keywords

    def paint(self, painter, option, index):
        """
        Paint a single cell using HTML rendering, highlighting configured keywords.

        Behavior:
        - Fills the background depending on selection state.
        - Converts the cell text to HTML with keyword highlighting.
        - Uses QTextDocument to render the HTML with wrapping.
        - Draws the document contents with a small padding offset.

        Args:
            painter (QPainter):
                Painter used for drawing.
            option (QStyleOptionViewItem):
                Style and geometry information for the item.
            index (QModelIndex):
                Model index for the cell being painted.

        Returns:
            None
        """
        text = index.data()
        if not text:
            return super().paint(painter, option, index)

        painter.save()

        # Draw background depending on selection state
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, option.backgroundBrush)

        # Convert keywords to HTML-marked-up string
        html = self._highlight_keywords(text)

        # Use QTextDocument for proper HTML rendering and line wrapping
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setHtml(html)
        doc.setTextWidth(option.rect.width() - 8)  # Account for horizontal padding

        # Offset drawing to avoid touching borders
        painter.translate(option.rect.topLeft() + QPoint(4, 4))
        doc.drawContents(painter)

        painter.restore()

    def _highlight_keywords(self, text):
        """
        Convert raw text into HTML with keyword highlighting.

        This method:
        - Escapes HTML special characters (&, <, >).
        - Converts newline characters to <br>.
        - Wraps each keyword occurrence with:
            <span style='color:red'>...</span>

        Note:
            This implementation performs simple string replacement and does not
            use regex or word-boundary matching.

        Args:
            text (str):
                Original cell text.

        Returns:
            str:
                HTML-formatted string with highlighted keywords.
        """
        escaped_text = (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>")
        )

        for kw in self.keywords:
            if not kw:
                continue
            escaped_kw = kw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            escaped_text = escaped_text.replace(
                escaped_kw, f"<span style='color:red'>{escaped_kw}</span>"
            )

        return escaped_text

    def sizeHint(self, option, index):
        """
        Return the preferred size for a cell based on HTML-rendered content.

        Computes the document size using QTextDocument with the same width constraints
        used during painting, then adds padding so the content does not touch borders.

        Args:
            option (QStyleOptionViewItem):
                Style and geometry information for the item.
            index (QModelIndex):
                Model index for the cell.

        Returns:
            QSize:
                Preferred size for the rendered cell content.
        """
        text = index.data()
        if not text:
            return super().sizeHint(option, index)

        html = self._highlight_keywords(text)
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setHtml(html)
        doc.setTextWidth(option.rect.width() - 8)

        return doc.size().toSize() + QSize(8, 8)  # padding