# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/generator/utils/slide_exporter.py

Slide export pipeline for converting generator slide data into
overlay-ready slide blocks.

This module defines the SlideExporter class, which takes structured
slide dictionaries produced by the generator UI and transforms them
into a flattened sequence of slides suitable for real-time overlay
display. The exporter applies style-specific rules such as line
segmentation, verse splitting, and style normalization.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

from core.generator.utils.text_splitter import split_by_length
from core.generator.utils.segment_utils import segment_lyrics_for_export

class SlideExporter:
    """
    Convert generator-format slides into overlay-ready slide blocks.

    This exporter applies style-specific transformation rules, including
    automatic line splitting, slide segmentation, and style normalization.

    Supported styles and behaviors:
    - lyrics / hymn / anthem:
        * Lyrics are split into two-line slides using blank-line boundaries.
        * Hymn slides are exported as "lyrics".
        * Anthem slides preserve caption and optional choir name.
    - verse:
        * Each (reference, verse) pair is split by character length.
    - respo:
        * Each response line is exported as an individual verse-style slide.
    - intro / blank:
        * Passed through with minimal transformation.
    - other styles:
        * Passed through unchanged.

    Args:
        settings (dict | None):
            Optional exporter settings.
            Supported keys:
            - "max_chars" (int): Maximum characters per text chunk.
    """

    def __init__(self, settings=None):
        """
        Initialize the slide exporter.

        Args:
            settings (dict | None):
                Optional configuration dictionary.
                If provided, "max_chars" controls the maximum number of
                characters allowed per exported text block.
        """
        self.max_chars = (settings or {}).get("max_chars", 60)

    def export(self, raw_slides: list[dict]) -> list[dict]:
        """
        Transform generator slides into a flat list of overlay slides.

        The exporter iterates over generator-format slide dictionaries
        and applies style-dependent rules to produce a sequence of
        overlay-ready slides.

        Args:
            raw_slides (list[dict]):
                List of slide dictionaries produced by the generator.
                Each dictionary is expected to include at least:
                - "style"
                - "caption"
                - "headline"

        Returns:
            list[dict]:
                A flattened list of slide dictionaries suitable for
                overlay display.
        """
        output = []

        for slide in raw_slides:
            style = slide.get("style", "lyrics")
            caption = slide.get("caption", "").strip()
            headline = slide.get("headline", "").strip()
            image_path = slide.get("image_path", "")

            # Lyrics, Hymn, Anthem
            if style in {"lyrics", "anthem", "hymn"}:
                if style == "anthem":
                    # Extract choir name if not separately stored
                    caption_main = slide.get("caption", "").strip()
                    caption_choir = slide.get("caption_choir", "").strip()
                    if not caption_choir:
                        parts = caption_main.split()
                        if len(parts) == 2:
                            caption_main, caption_choir = parts[0], parts[1]
                        else:
                            caption_choir = ""
                    slide["caption"] = caption_main
                    slide["caption_choir"] = caption_choir

                split_slides = segment_lyrics_for_export(slide)
                for s in split_slides:
                    export_style = "lyrics" if style == "hymn" else style
                    s["style"] = export_style
                    if style == "anthem":
                        s["caption_choir"] = slide.get("caption_choir", "")
                    output.append(s)
                continue

            # Bible verses
            elif style == "verse":
                lines = [line.strip() for line in headline.splitlines() if line.strip()]
                i = 0
                while i < len(lines) - 1:
                    ref = lines[i]
                    verse_text = lines[i + 1]
                    chunks = self._split_text(verse_text)
                    for chunk in chunks:
                        output.append({
                            "style": "verse",
                            "caption": ref,
                            "headline": chunk
                        })
                    i += 2

                if i < len(lines):
                    output.append({
                        "style": "verse",
                        "caption": lines[i],
                        "headline": ""
                    })
                continue

            # Responsive reading (each line = 1 slide)
            elif style == "respo":
                for line in headline.splitlines():
                    if line.strip():
                        output.append({
                            "style": "verse",
                            "caption": caption,
                            "headline": line.strip()
                        })
                continue

            # Intro or blank
            elif style == "intro":
                output.append({
                    "style": "intro",
                    "caption": caption,
                    "headline": headline
                })
                continue

            elif style == "blank":
                output.append({
                    "style": "blank",
                    "caption": "",
                    "headline": ""
                })
                continue

            # Passthrough for other styles
            else:
                output.append({
                    "style": style,
                    "caption": caption,
                    "headline": headline
                })

        return output

    def _split_text(self, text: str) -> list[str]:
        """
        Split a text string into smaller chunks by character count.

        This helper delegates to `split_by_length`, using the configured
        maximum character length for exported slides.

        Args:
            text (str):
                Input text to be split.

        Returns:
            list[str]:
                List of text chunks, each within the configured length.
        """
        return split_by_length(text, max_chars=self.max_chars)