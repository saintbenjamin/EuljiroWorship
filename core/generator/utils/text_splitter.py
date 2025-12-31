# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/generator/utils/text_splitter.py

Provides utility function for splitting text into chunks of specified length.

This module contains a simple text segmentation helper used primarily during
slide export. Its main purpose is to prevent excessively long lines from being
rendered as a single overlay line by splitting text into display-friendly units.

Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
Telephone: +82-2-2266-3070
E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
Copyright (c) 2025 The Eulji-ro Presbyterian Church.
License: MIT License with Attribution Requirement (see LICENSE file for details)
"""

import textwrap

def split_by_length(text: str, max_chars: int = 50) -> list[str]:
    """
    Split a text string into multiple chunks constrained by a maximum character length.

    This helper uses Python's `textwrap.wrap()` to break a long string into
    word-aware segments. Line breaks are inserted at appropriate word boundaries
    whenever possible, ensuring that each resulting chunk does not exceed
    `max_chars` characters.

    This function is intentionally simple and presentation-oriented:
    - It does not preserve original newlines.
    - It does not apply hyphenation.
    - It assumes the input text is a single logical paragraph.

    Typical use cases include:
    - Splitting long Bible verses for overlay display.
    - Breaking lyrics or responsive readings into readable slide units.

    Args:
        text (str): Input text to be split.
        max_chars (int): Maximum number of characters allowed per chunk.
            Defaults to 50.

    Returns:
        list[str]: A list of text chunks, each suitable for individual slide display.
    """
    return textwrap.wrap(text.strip(), width=max_chars)