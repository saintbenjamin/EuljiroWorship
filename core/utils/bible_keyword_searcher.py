# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/utils/bible_keyword_searcher.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Performs keyword-based search on Bible text files for EuljiroBible.

This module provides lightweight, in-memory keyword search functionality
over a single Bible version JSON file. It is designed for fast interactive
search in both CLI and GUI contexts.

Supported search modes include:
- Word-based AND search
- Whitespace-insensitive (compact) substring search

Search results include both raw verse text and HTML-highlighted text
for immediate display use.
"""

import os
import json
import re
from core.config import paths

class BibleKeywordSearcher:
    """
    Keyword-based Bible verse search engine.

    This class loads a single Bible version into memory and provides
    multiple keyword search strategies over the verse text.

    Search results are returned as structured dictionaries containing
    verse location metadata and both raw and highlighted text, making
    them suitable for direct rendering in UI components.
    """

    def __init__(self, version: str = "개역개정"):
        """
        Initialize the keyword searcher with a specific Bible version.

        The corresponding Bible JSON file is loaded into memory at
        initialization time.

        Args:
            version (str):
                Bible version name without file extension
                (e.g., "개역개정", "NKRV").

        Returns:
            None

        Raises:
            FileNotFoundError:
                If the specified Bible version file does not exist.
        """
        self.version = version
        filepath = os.path.join(paths.BIBLE_DATA_DIR, f"{version}.json")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Bible data file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        with open(paths.STANDARD_BOOK_FILE, "r", encoding="utf-8") as f:
            self.name_map = json.load(f)

    def search_compact_string(self, keyword: str, limit: int = 100) -> list[dict]:
        """
        Perform whitespace-insensitive substring search.

        All whitespace is removed from both the keyword and verse text
        before matching, allowing detection of continuous phrases
        regardless of spacing differences.

        Args:
            keyword (str):
                Input search string.
            limit (int, optional):
                Maximum number of results to return. Defaults to 100.

        Returns:
            list[dict]:
                List of matching verse dictionaries, each containing:
                - book
                - chapter
                - verse
                - text
                - highlighted
        """
        results = []
        stripped = keyword.strip()
        compressed = stripped.replace(" ", "")  # remove all spaces
        pattern = re.compile(re.escape(compressed), re.IGNORECASE)

        for book, chapters in self.data.items():
            for chapter_num, verses in chapters.items():
                for verse_num, verse_text in verses.items():
                    normalized = verse_text.replace(" ", "")
                    if compressed in normalized:
                        # Apply highlighting to the raw verse text
                        highlighted = pattern.sub(
                            lambda m: f'<span style="color:red; font-weight:bold;">{m.group(0)}</span>',
                            verse_text
                        )
                        results.append({
                            "book": book,
                            "chapter": int(chapter_num),
                            "verse": int(verse_num),
                            "text": verse_text.strip(),
                            "highlighted": highlighted.strip()
                        })

                        if len(results) >= limit:
                            return results
        return results

    def search_wordwise_and(self, keyword: str, limit: int = 100) -> list[dict]:
        """
        Perform word-based AND search.

        All whitespace-separated words in the keyword must appear
        somewhere in the verse text for a match to occur.

        Args:
            keyword (str):
                Space-separated search terms.
            limit (int, optional):
                Maximum number of results to return. Defaults to 100.

        Returns:
            list[dict]:
                List of matching verse dictionaries with highlighted terms.
        """
        results = []
        words = keyword.strip().split()
        regexes = [re.compile(re.escape(w), re.IGNORECASE) for w in words if w]

        for book, chapters in self.data.items():
            for ch_str, verses in chapters.items():
                for v_str, text in verses.items():
                    if all(r.search(text) for r in regexes):
                        # Apply highlight
                        highlighted = text
                        for r in regexes:
                            highlighted = r.sub(lambda m: f'<span style="color:red; font-weight:bold;">{m.group()}</span>', highlighted)
                        results.append({
                            "book": book,
                            "chapter": int(ch_str),
                            "verse": int(v_str),
                            "text": text,
                            "highlighted": highlighted
                        })
        return results

    def search(self, keyword: str, limit: int = 100, mode: str = "and") -> list[dict]:
        """
        Unified keyword search interface.

        This method dispatches to the appropriate search strategy
        based on the selected mode.

        Args:
            keyword (str):
                Input keyword or phrase.
            limit (int, optional):
                Maximum number of results to return.
            mode (str, optional):
                Search mode selector.
                - "and": word-based AND search (default)
                - "compact": whitespace-insensitive substring search

        Returns:
            list[dict]:
                Search result list.
        """
        if mode == "compact":
            return self.search_compact_string(keyword, limit)
        return self.search_wordwise_and(keyword, limit)

    def count_keywords(self, results: list[dict], keywords: list[str]) -> dict[str, int]:
        """
        Count total occurrences of each keyword across search results.

        This method performs full regex-based counting (case-insensitive)
        over the raw verse text of each search result.

        Args:
            results (list[dict]):
                List of verse dictionaries returned from a search.
            keywords (list[str]):
                List of keywords to count.

        Returns:
            dict[str, int]:
                Mapping of keyword -> total occurrence count.
        """
        counts = {w: 0 for w in keywords}
        for r in results:
            text = r["text"]
            for w in keywords:
                counts[w] += len(re.findall(re.escape(w), text, re.IGNORECASE))
        return counts