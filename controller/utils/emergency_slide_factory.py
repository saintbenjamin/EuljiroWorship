# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/controller/utils/emergency_slide_factory.py

Generates slide dictionaries for emergency captions.

This module defines `EmergencySlideFactory`, a utility that builds slide payloads
consumable by the slide controller / overlay pipeline.

Supported inputs:
- Bible references (parsed by `core.utils.bible_parser.parse_reference`)
- Manual fallback captions and messages
- Preset responsive readings (교독문) and hymns loaded from JSON files

Outputs:
- A list of slide dictionaries with keys: "style", "caption", "headline"

Notes:
- Bible verse text is wrapped into smaller chunks (currently width=50) to avoid
  overly long single-slide lines.
- Version display aliases are loaded from `paths.ALIASES_VERSION_FILE`.

Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
Telephone: +82-2-2266-3070
E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
Copyright (c) 2025 The Eulji-ro Presbyterian Church.
License: MIT License with Attribution Requirement (see LICENSE file for details)
"""

import os
import json
import textwrap

from core.config import paths
from core.utils.bible_data_loader import BibleDataLoader
from core.utils.bible_parser import parse_reference

class EmergencySlideFactory:
    """
    Factory for constructing emergency slide blocks.

    This class converts user-facing emergency inputs into a list of slide dicts.

    Primary responsibilities:
    - Detect whether the first line is a Bible reference via `parse_reference()`
    - If a reference is valid, retrieve verses using `BibleDataLoader`
    - Wrap long verse text into multiple slides using `textwrap.wrap`
    - If not a reference, build a fallback "manual" slide payload
    - Load preset materials:
      - Responsive readings (respo) from JSON
      - Hymns from JSON

    Slide dict schema:
        {
            "style": str,     # e.g., "verse", "lyrics", "greet", ...
            "caption": str,   # title / reference line
            "headline": str,  # main body text shown on screen
        }
    """

    def __init__(self, bible_loader=None):
        """
        Initialize the factory.

        Loads Bible version display aliases from `paths.ALIASES_VERSION_FILE` and
        prepares a `BibleDataLoader` instance (either the provided one or a default).

        Args:
            bible_loader (BibleDataLoader | None):
                Optional custom Bible loader. If None, a default `BibleDataLoader()`
                is created and used.

        Returns:
            None
        """
        with open(paths.ALIASES_VERSION_FILE, encoding="utf-8") as f:
            self.VERSION_ALIASES = json.load(f)
        self.loader = bible_loader or BibleDataLoader()

    def create_from_input(self, line1: str, line2: str, version: str = None) -> list[dict]:
        """
        Create emergency slides from a pair of user input lines.

        Behavior:
        - If `line1` is parsed as a Bible reference (e.g., "요 3:16", "요한복음 3:16"),
        this method retrieves the verse text and returns verse-style slides.
        - If the reference represents a full chapter request (verse_range like (1, -1)),
        it expands the range to the chapter's maximum verse count when possible.
        - If `line1` is NOT a valid reference, it falls back to a single manual slide
        where `line1` becomes the caption and `line2` becomes the headline.

        Args:
            line1 (str):
                First line of user input. Interpreted as either a Bible reference
                or a manual caption.
            line2 (str):
                Second line of user input. Interpreted as either ignored (when the
                first line is a valid reference) or a manual headline/message.
            version (str | None):
                Preferred Bible version name to use when resolving verse text.
                If None, the loader's default/available version list is used.

        Returns:
            list[dict]:
                A list of slide dictionaries. Returns an empty list if no valid
                output can be produced (e.g., empty manual input or failed verse load).
        """
        parsed = parse_reference(line1)
        if parsed:
            book_id, chapter, verses = parsed

            # Handle full chapter request (verse_range = (1, -1))
            if isinstance(verses, tuple) and verses[1] == -1:
                try:
                    max_verse = len(self.loader.get_verses(version)[book_id][str(chapter)])
                    verses = list(range(1, max_verse + 1))
                except Exception as e:
                    print(f"[ERROR] Failed to expand full chapter: {e}")
                    return []

            return self.build_bible_slides(book_id, chapter, verses, version)

        # Fallback for custom manual input
        caption = line1.strip()
        headline = line2.strip()

        if not caption and not headline:
            print("[DEBUG] No input provided. Empty slide list returned.")
            return []

        print(f"[DEBUG] Manual fallback: caption='{caption}', headline='{headline}'")
        return [{
            "style": "verse",
            "caption": caption or "대한예수교장로회(통합) 을지로교회",
            "headline": headline or "(내용 없음)"
        }]

    def build_bible_slides(self, book_id, chapter, verses, version=None) -> list[dict]:
        """
        Build verse-style slides for the given Bible location and verse range.

        This method attempts to retrieve verse text using `BibleDataLoader.get_verse()`.
        If `version` is provided, it tries that version first; otherwise it iterates
        available versions and returns the first successful slide set.

        Each verse is wrapped using `textwrap.wrap(..., width=50)` to avoid overly long
        single lines, producing multiple slides per verse when needed.

        Args:
            book_id (str):
                Internal Bible book identifier (e.g., "John").
            chapter (int):
                Chapter number.
            verses (list[int] | tuple[int, int]):
                Verse numbers to include. The implementation currently uses
                `min(verses)` and `max(verses)` to define an inclusive range.
            version (str | None):
                Preferred Bible version name. If None, tries multiple versions.

        Returns:
            list[dict]:
                A list of verse-style slide dictionaries. If verse retrieval fails
                for all attempted versions, returns an empty list.
        """
        result = []
        start, end = min(verses), max(verses)
        target_versions = [version] if version else self.loader.aliases_version

        for ver in target_versions:
            alias = self.VERSION_ALIASES.get(ver, ver)
            slides = []
            for verse_num in range(start, end + 1):
                try:
                    verse_text = self.loader.get_verse(ver, book_id, chapter, verse_num)
                    reftext = f"{self.loader.get_standard_book(book_id, 'ko')} {chapter}장 {verse_num}절 ({alias})"
                    chunks = textwrap.wrap(verse_text.strip(), width=50)
                    for chunk in chunks:
                        slides.append({
                            "style": "verse",
                            "caption": reftext,
                            "headline": chunk
                        })
                except Exception:
                    continue
            if slides:
                return slides

        return result

    def create_from_respo(self, number: int) -> list[dict]:
        """
        Load a responsive reading (교독문) JSON by number and generate slides.

        The expected JSON format contains:
        - "title": str (optional)
        - "slides": list of entries, each typically containing:
            - "speaker": str
            - "headline": str

        For each entry, one slide is created containing a single speaker-response
        line formatted in an HTML-like style (e.g., "<b>...</b>").

        Args:
            number (int):
                Responsive reading number (e.g., 123).

        Returns:
            list[dict]:
                A list of slide dictionaries (style "verse").
                If loading fails, returns a one-slide fallback with an error message.
        """
        path = os.path.join("data", "respo", f"responsive_{number:03d}.json")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", f"성시교독 {number}번")
                slides_raw = data.get("slides", [])

                slides = []
                for entry in slides_raw:
                    speaker = entry.get("speaker", "").strip()
                    headline = entry.get("headline", "").strip()
                    if speaker or headline:
                        slides.append({
                            "style": "verse",
                            "caption": title,
                            "headline": f"<b>{speaker}:</b> {headline}"
                        })

                return slides

        except Exception:
            return [{
                "style": "verse",
                "caption": f"성시교독 {number}번",
                "headline": f"(교독문 {number}번을 불러올 수 없습니다)"
            }]

    def format_responsive_text(self, slides_raw: list[dict]) -> str:
        """
        Format responsive reading entries into a single joined string.

        Each entry is converted into one line using an HTML-like emphasis for the
        speaker name:
            "<b>{speaker}:</b> {headline}"

        Args:
            slides_raw (list[dict]):
                Raw entry list, where each entry may include:
                - "speaker": str
                - "headline": str

        Returns:
            str:
                A newline-joined formatted text block. Empty entries are skipped.
        """
        lines = []
        for entry in slides_raw:
            speaker = entry.get("speaker", "").strip()
            headline = entry.get("headline", "").strip()
            if speaker or headline:
                lines.append(f"<b>{speaker}:</b> {headline}")
        return "\n".join(lines)

    def create_from_hymn(self, number: int) -> list[dict]:
        """
        Load a hymn JSON by number and split it into lyric slides.

        The expected JSON format contains:
        - "title": str (optional)
        - "headline": str (lyrics text, typically multi-line)

        Lyrics are split into chunks of two lines per slide.

        Args:
            number (int):
                Hymn number (e.g., 88).

        Returns:
            list[dict]:
                A list of slide dictionaries with style "lyrics".
                If loading fails, returns a one-slide fallback with an error message.
        """
        path = os.path.join("data", "hymns", f"hymn_{number:03d}.json")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", f"새찬송가 {number}장")
                body = data.get("headline", "")

                lines = body.strip().split("\n")
                slides = []
                for i in range(0, len(lines), 2):  # Group by 2 lines
                    chunk = "\n".join(lines[i:i+2]).strip()
                    if chunk:
                        slides.append({
                            "style": "lyrics",
                            "caption": title,
                            "headline": chunk
                        })

                return slides

        except Exception as e:
            return [{
                "style": "lyrics",
                "caption": f"새찬송가 {number}장",
                "headline": f"(찬송가 {number}번을 불러올 수 없습니다)"
            }]

    def create_manual_slide(self, style: str, caption: str, text: str) -> list[dict]:
        """
        Generate slide(s) from manually provided content.

        Behavior:
        - If `style` is "lyrics", the input text is split by lines and grouped
        into 2-line chunks per slide.
        - For all other styles, a single slide is produced as-is.

        Args:
            style (str):
                Internal slide style (e.g., "verse", "greet", "lyrics").
            caption (str):
                Caption/title string shown above or alongside the main text.
            text (str):
                Main body text for the slide(s).

        Returns:
            list[dict]:
                List of slide dictionaries ready to be exported.
        """
        if style == "lyrics":
            lines = text.strip().split("\n")
            slides = []
            for i in range(0, len(lines), 2):
                chunk = "\n".join(lines[i:i+2]).strip()
                if chunk:
                    slides.append({
                        "style": "lyrics",
                        "caption": caption,
                        "headline": chunk
                    })
            return slides
        else:
            return [{
                "style": style,
                "caption": caption,
                "headline": text
            }]