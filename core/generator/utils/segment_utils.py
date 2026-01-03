# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/utils/segment_utils.py

Utilities for segmenting slide data during export.

This module contains helper functions used at export time to transform
generator slide data into overlay-ready slide units. In particular, it
handles segmentation of multi-line lyrics content into multiple slides
using blank-line boundaries and fixed two-line grouping rules.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

def segment_lyrics_for_export(data: dict) -> list[dict]:
    """
    Split a single 'lyrics' slide into multiple export-ready slides.

    This function takes a lyrics-style slide dictionary and divides its
    multiline headline text into smaller slides according to the following
    rules:

    - Blank lines force a slide break.
    - Non-empty lines are grouped into slides of up to two lines.
    - Remaining lines are emitted as a final slide if fewer than two.

    Args:
        data (dict):
            Slide dictionary with at least the keys:
            - "style": expected to be "lyrics"
            - "caption": title of the song
            - "headline": multiline lyrics text

    Returns:
        list[dict]:
            A list of slide dictionaries, each containing:
            - "style"
            - "caption"
            - "headline" (two lines or fewer)
    """
    style = data.get("style", "lyrics")
    caption = data.get("caption", "")
    headline = data.get("headline", "")

    lines = [line.strip() for line in headline.splitlines()]
    slides = []
    buffer = []

    for line in lines:
        if not line:
            if buffer:
                slides.append({
                    "style": style,
                    "caption": caption,
                    "headline": "\n".join(buffer)
                })
                buffer = []
            continue

        buffer.append(line)
        if len(buffer) == 2:
            slides.append({
                "style": style,
                "caption": caption,
                "headline": "\n".join(buffer)
            })
            buffer = []

    if buffer:
        slides.append({
            "style": style,
            "caption": caption,
            "headline": "\n".join(buffer)
        })

    return slides