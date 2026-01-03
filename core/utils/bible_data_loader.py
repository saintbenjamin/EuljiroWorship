# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/utils/bible_data_loader.py

Handles lazy loading and caching of Bible text and metadata from JSON sources.

This module provides a unified data access layer for Bible-related resources,
including:

- Bible version aliases
- Book name aliases
- Canonical book names
- Custom sort order
- Full Bible text data

All Bible text JSON files are loaded lazily and cached in memory on first access
to minimize startup cost and disk I/O.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

import os
import json

from core.config import paths
from core.utils.logger import log_error

class BibleDataLoader:
    """
    Lazy-loading data manager for Bible text and metadata.

    This class loads and caches Bible-related JSON resources on demand,
    including version metadata, book aliases, canonical book names, and
    full Bible text files.

    Bible text files are loaded per version only when first requested
    and stored in an internal cache to avoid repeated disk access.

    The class is shared by both EuljiroBible and EuljiroWorship systems
    and therefore includes several compatibility helper methods.
    """

    def __init__(self, json_dir=None, text_dir=None):
        """
        Initialize the Bible data loader.

        Optional directory overrides can be supplied for testing or
        alternative data layouts.

        Args:
            json_dir (str, optional):
                Directory containing Bible metadata JSON files
                (aliases, canonical names, sort order).
            text_dir (str, optional):
                Directory containing Bible text JSON files.
        
        Returns:
            None
        """
        self.json_dir = json_dir or paths.BIBLE_NAME_DIR
        self.text_dir = text_dir or paths.BIBLE_DATA_DIR

        # Load version and book aliases, canonical book names, and sort order
        self.aliases_version = self._load_json(os.path.join(self.json_dir, "aliases_version.json"))
        self.aliases_book = self._load_json(os.path.join(self.json_dir, "aliases_book.json"))
        self.standard_book = self._load_json(os.path.join(self.json_dir, "standard_book.json"))
        self.sort_order = self._load_json(os.path.join(self.json_dir, "your_sort_order.json"))

        self.data = {}  # Cache for loaded Bible texts

    def get_verses(self, version):
        """
        Retrieve all verses for a given Bible version.

        The version data is loaded from disk only once and cached
        internally for subsequent access.

        Args:
            version (str):
                Bible version key (e.g. "NKRV", "KJV").

        Returns:
            dict:
                Nested dictionary structure containing the full Bible
                text for the specified version.
        """
        if version not in self.data:
            try:
                with open(os.path.join(self.text_dir, f"{version}.json"), "r", encoding="utf-8") as f:
                    self.data[version] = json.load(f)
            except Exception as e:
                log_error(f"[BibleDataLoader] Failed to load version '{version}': {e}")
                self.data[version] = {}
        return self.data[version]

    def get_books_for_version(self, version):
        """
        Return the list of books available in a given Bible version.

        Args:
            version (str):
                Bible version key.

        Returns:
            list:
                List of book identifiers present in the version.
        """
        verses = self.get_verses(version)
        return list(verses.keys()) if verses else []

    def _load_json(self, file_path):
        """
        Safely load a JSON file and return its contents.

        If loading fails, an empty dictionary is returned and a warning
        is printed to the console.

        Args:
            file_path (str):
                Absolute path to the JSON file.

        Returns:
            dict:
                Parsed JSON content, or an empty dict on failure.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to load {file_path}: {e}")
            return {}

    def get_standard_book(self, book_id: str, lang_code: str) -> str:
        """
        Return the localized canonical name of a Bible book.

        Args:
            book_id (str):
                Canonical book identifier (e.g. "John").
            lang_code (str):
                Language code (e.g. "ko", "en").

        Returns:
            str:
                Localized book name if available, otherwise the book ID.
        """
        return self.standard_book.get(book_id, {}).get(lang_code, book_id)

    def get_sort_key(self):
        """
        Return a sorting key function for Bible version names.

        The key function sorts versions using a predefined regional
        prefix order followed by lexicographical ordering.

        This method is required by both GUI and CLI code paths.
        DO NOT DELETE.

        Args:
            None

        Returns:
            function:
                Callable suitable for use as the `key` argument in sorted().
        """
        def sort_key(version_name: str):
            prefix = version_name.split()[0]
            return (self.sort_order.get(prefix, 99), version_name)
        return sort_key

    def load_version(self, version_key):
        """
        Explicitly load a Bible version into memory.

        This method forces loading even if lazy access has not yet occurred.

        Args:
            version_key (str):
                Bible version key (filename without extension).

        Returns:
            None
        """
        path = os.path.join(self.text_dir, f"{version_key}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data[version_key] = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load version {version_key}: {e}")
            self.data[version_key] = {}

    def load_versions(self, target_versions=None):
        """
        Load multiple Bible versions into memory.

        If no target list is provided, all available versions
        in the text directory are loaded.

        Args:
            target_versions (list, optional):
                List of version keys to load.

        Returns:
            None
        """
        if target_versions is None:
            self.data.clear()
            target_versions = [
                fname.replace(".json", "")
                for fname in os.listdir(self.text_dir)
                if fname.endswith(".json")
            ]
        for v in target_versions:
            self.load_version(v)

    def get_max_verse(self, version, book, chapter):
        """
        Return the maximum verse number for a given chapter.

        Args:
            version (str):
                Bible version key.
            book (str):
                Book identifier.
            chapter (int):
                Chapter number.

        Returns:
            int:
                Maximum verse number, or 0 if unavailable.
        """
        version_data = self.data.get(version)
        if not version_data:
            return 0
        book_data = version_data.get(book)
        if not book_data:
            return 0
        chapter_data = book_data.get(str(chapter))
        if not chapter_data:
            return 0
        return max(map(int, chapter_data.keys()), default=0)

    def extract_verses(self, versions, book, chapter, verse_range):
        """
        Extract a specific verse range across multiple Bible versions.

        Args:
            versions (list):
                List of Bible version keys.
            book (str):
                Book identifier.
            chapter (int):
                Chapter number.
            verse_range (tuple):
                (start, end) or (start, -1) for full chapter.

        Returns:
            dict:
                Nested dictionary of extracted verses grouped by version.
        """
        results = {}
        chapter_str = str(chapter)
        start, end = verse_range

        for version in versions:
            verses = self.get_verses(version)
            book_data = verses.get(book, {})
            chapter_data = book_data.get(chapter_str, {})
            if not chapter_data:
                continue

            results.setdefault(version, {}).setdefault(book, {}).setdefault(chapter_str, {})

            # Full chapter case
            if end == -1:
                for verse_str, text in chapter_data.items():
                    if text:
                        results[version][book][chapter_str][verse_str] = text
            # Partial range case
            else:
                for i in range(start, end + 1):
                    verse_str = str(i)
                    text = chapter_data.get(verse_str)
                    if text:
                        results[version][book][chapter_str][verse_str] = text

        return results

    def get_verses_for_display(self, versions=None, book=None, chapter=None, verse_range=None):
        """
        Return either a filtered verse subset or full Bible data.

        Args:
            versions (list, optional):
                Bible version keys.
            book (str, optional):
                Book identifier.
            chapter (int, optional):
                Chapter number.
            verse_range (tuple, optional):
                Verse range.

        Returns:
            dict:
                Structured Bible text data.
        """
        if versions and book and chapter and verse_range:
            return self.extract_verses(versions, book, chapter, verse_range)
        else:
            return self.get_verses()

    def get_book_alias(self, lang_code="ko") -> dict:
        """
        Return mapping of book IDs to localized aliases.

        Args:
            lang_code (str):
                Language code.

        Returns:
            dict:
                Mapping of book_id -> localized name.
        """
        return {
            book_id: data.get(lang_code, book_id)
            for book_id, data in self.standard_book.items()
        }

    def get_version_alias(self, lang_code="ko") -> dict:
        """
        Return mapping of Bible version keys to localized aliases.

        Args:
            lang_code (str):
                Language code.

        Returns:
            dict:
                Mapping of version_key -> alias string.
        """
        alias_map = {}
        for k, v in self.aliases_version.items():
            if isinstance(v, dict):
                alias_map[k] = v.get("aliases", {}).get(lang_code, k)
            else:
                alias_map[k] = v
        return alias_map

    # For compatibility with EuljiroWorship system    
    def get_verse(self, version: str, book: str, chapter: int, verse: int) -> str | None:
        """
        Retrieve a single verse from the loaded Bible data.

        This method exists for compatibility with the EuljiroWorship system.

        Args:
            version (str):
                Bible version key.
            book (str):
                Book identifier.
            chapter (int):
                Chapter number.
            verse (int):
                Verse number.

        Returns:
            str | None:
                Verse text if found, otherwise None.
        """
        verses = self.get_verses(version)
        return (
            verses.get(book, {})
                .get(str(chapter), {})
                .get(str(verse))
        )
