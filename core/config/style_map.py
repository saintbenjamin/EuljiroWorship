# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/config/style_map.py

Defines mappings between internal slide style identifiers and
their Korean display names used in the generator UI.

This module serves as the single source of truth for slide style naming
across the system. It provides:

- `STYLE_ALIASES`: Mapping from internal style keys (used in JSON/export)
  to Korean labels displayed in the UI.
- `REVERSE_ALIASES`: Reverse lookup mapping from Korean labels back to
  internal style keys.
- `STYLE_LIST`: Ordered list of Korean display names, primarily used
  to populate dropdown menus in the slide generator table.

By centralizing these mappings, the generator UI, data manager,
and exporter remain consistent and resilient to future style additions
or renaming.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

# ───── Internal style to Korean display name ─────
STYLE_ALIASES = {
    "corner": "코너자막",     # Corner overlay
    "hymn":   "새찬송가",     # Hymnal number
    "lyrics": "찬양가사",     # General praise lyrics
    "respo":  "성시교독",     # Responsive reading
    "prayer": "대표기도",     # Representative prayer
    "verse":  "성경봉독",     # Scripture reading
    "anthem": "찬양제목",     # Anthem title
    "greet":  "메세지란",     # Custom greeting/message
    "intro":  "시작화면",     # Introductory screen
    "blank":  "공백화면",     # Empty screen
    "image":  "그림화면",     # Image display
    "video":  "영상재생",     # Video display 
}

# ───── Reverse mapping: Korean → internal key ─────
REVERSE_ALIASES = {v: k for k, v in STYLE_ALIASES.items()}

# ───── List of all Korean display names (used in UI dropdowns) ─────
STYLE_LIST = list(STYLE_ALIASES.values())