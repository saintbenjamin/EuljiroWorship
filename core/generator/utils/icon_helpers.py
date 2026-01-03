# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/utils/icon_helpers.py

Utility helpers for applying SVG icons to Qt widgets.

This module provides small helper functions used throughout the slide
generator UI to standardize icon handling, including resolving icon
paths and applying SVG icons to QPushButton instances.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import os
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from core.config import paths

def set_svg_icon(button: QPushButton, svg_path: str, size: int = 24, text: str | None = None):
    """
    Apply an SVG icon to a QPushButton.

    This helper sets the button icon, icon size, and optionally a text
    label. If no text is provided, the button is rendered in icon-only mode.

    Args:
        button (QPushButton):
            Target button to modify.
        svg_path (str):
            Absolute or resolved path to the SVG icon file.
        size (int, optional):
            Icon width and height in pixels. Defaults to 24.
        text (str | None, optional):
            Optional button label. If None, no text is shown.

    Returns:
        None
    """
    icon = QIcon(svg_path)
    button.setIcon(icon)
    button.setIconSize(QSize(size, size))

    if text:
        button.setText(text)
        button.setLayoutDirection(Qt.LeftToRight)
    else:
        button.setText("")

def get_icon_path(name: str) -> str:
    """
    Resolve the full filesystem path of an icon file.

    This function prepends the configured icon directory path to the
    given icon filename.

    Args:
        name (str):
            Icon filename (e.g., "save.svg").

    Returns:
        str:
            Absolute path to the icon file.
    """
    return os.path.join(paths.ICON_DIR, name)