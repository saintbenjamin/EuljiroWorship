# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/utils/bible_parser.py

Parses Bible reference strings and resolves book name aliases from user input.

This module provides lightweight parsing utilities for converting
user-entered Bible reference strings into structured components
(book ID, chapter, verse range).

Key responsibilities:

- Resolve book name aliases into canonical internal IDs
- Parse flexible reference formats such as:
  - "요 3"
  - "요한복음 3:16"
  - "John 3:14-16"
- Support chapter-only references and full verse ranges

The parser is intentionally permissive and designed for use in
both CLI and GUI contexts.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import re
import json

from core.config import paths

# ─────────────────────────────────────────────
# Load book name aliases from JSON at module load time
try:
    with open(paths.ALIASES_BOOK_FILE, encoding="utf-8") as f:
        BOOK_ALIASES = json.load(f)
except Exception as e:
    print(f"[!] Failed to load aliases_book.json: {e}")
    BOOK_ALIASES = {}
# ─────────────────────────────────────────────

def resolve_book_name(name: str, lang_map: dict = None, lang_code: str = "ko") -> str | None:
    """
    Resolve a user-provided book name to a canonical internal book ID.

    This function attempts resolution using multiple strategies:
    1. Direct alias matching from `BOOK_ALIASES`
    2. Reverse matching against canonical IDs
    3. Optional fallback using localized names from `standard_book.json`

    All comparisons are performed using normalized strings
    (lowercased, whitespace and dot characters removed).

    Args:
        name (str):
            Raw book name from user input
            (e.g., "요삼", "1Jn", "Genesis").
        lang_map (dict, optional):
            Mapping loaded from `standard_book.json`,
            structured as { book_id: { "ko": ..., "en": ... } }.
        lang_code (str, optional):
            Language key used when matching localized names.
            Defaults to "ko".

    Returns:
        str | None:
            Canonical internal book ID (e.g., "3John"),
            or None if no match is found.
    """
    if not name:
        return None

    raw = name.strip()
    normalized = raw.lower().replace(" ", "").replace(".", "")

    # 1. Try direct alias match (with normalization)
    for alias, canonical in BOOK_ALIASES.items():
        alias_norm = alias.strip().lower().replace(" ", "").replace(".", "")
        if normalized == alias_norm:
            return canonical

    # 2. Reverse match if name is already canonical
    for canonical in BOOK_ALIASES.values():
        if normalized == canonical.lower().replace(" ", "").replace(".", ""):
            return canonical

    # 3. Fallback: optional standard book name matching
    if lang_map:
        for key, names in lang_map.items():
            local = names.get(lang_code, "").lower().replace(" ", "").replace(".", "")
            en = names.get("en", "").lower().replace(" ", "").replace(".", "")
            if normalized == local or normalized == en:
                return key

    return None

def parse_reference(text: str):
    """
    Parse a Bible reference string into structured components.

    Supported input formats include:
        "<book> <chapter>"
        "<book> <chapter>:<verse>"
        "<book> <chapter>:<start>-<end>"

    Examples:
        "요 3"
        "요한복음 3:16"
        "John 3:14-16"

    If only a chapter is provided, the verse range is interpreted
    as the full chapter.

    Args:
        text (str):
            Raw reference string entered by the user.

    Returns:
        tuple[str, int, tuple[int, int]] | None:
            A tuple of (book_id, chapter_number, verse_range),
            where verse_range is (start, end) and end == -1
            indicates the full chapter.

            Returns None if parsing or resolution fails.
    """
    text = text.strip()

    # Modified regex to also match "<book> <chapter>" (verse omitted)
    m = re.match(r"(.+?)\s*(\d+)(?::(\d+)(?:-(\d+))?)?", text)
    if not m:
        return None

    book_str, chapter_str, verse_start_str, verse_end_str = m.groups()

    # Resolve book name using alias map
    book_id = resolve_book_name(book_str)
    if not book_id:
        return None

    # Convert string components to integers
    chapter = int(chapter_str)

    # Support chapter-only input (e.g., "John 3")
    if verse_start_str is None:
        return book_id, chapter, (1, -1)

    verse_start = int(verse_start_str)
    verse_end = int(verse_end_str) if verse_end_str else verse_start

    # Sanity check: verse range must be ascending
    if verse_end < verse_start:
        return None

    # Return all verses in range as tuple
    return book_id, chapter, (verse_start, verse_end)