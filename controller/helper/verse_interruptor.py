# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/controller/helper/verse_interruptor.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Watches :py:data:`core.config.paths.VERSE_FILE` and converts it into slide JSON
written to :py:data:`core.config.paths.SLIDE_FILE` for real-time display by the slide controller.

This module runs as a small background helper process. It uses `watchdog <https://pypi.org/project/watchdog/>`_ to
monitor the project base directory for changes to the :py:data:`core.config.paths.VERSE_FILE`, then
parses the content into one or more slide dictionaries.

Key behaviors:

- If the last line looks like a structured Bible reference header, it generates
  per-verse slides with wrapped lines (`textwrap.wrap <https://docs.python.org/3/library/textwrap.html#textwrap.wrap>`_) and style "verse".
- Otherwise, it treats the file as a free-form emergency message and generates
  style "lyrics" slides grouped by up to 2 lines (or by character budget).
- Before overwriting the slide file, it may create a backup at
  :py:data:`core.config.paths.SLIDE_BACKUP_FILE` (only if the backup file does not already exist).
"""

import sys, os
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ─────────────────────────────────────────────
# Add project root to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ─────────────────────────────────────────────

from core.config import paths
from core.config import constants

def parse_verse_output(file_path, max_chars=60):
    """
    Parse ``file_path`` into a list of slide dictionaries.

    The input file is interpreted as:

    - Structured mode: If the last line matches one of the expected header forms (e.g., ``<book> <chapter>장 ...``, ``<book> <chapter>:<verse>, ...``), the earlier lines are treated as verse body lines. Each verse line is wrapped to ``max_chars`` and converted into style "verse" slides.
    - Fallback mode: If no header pattern matches, the entire file is treated as a free-form emergency message. Non-empty lines are grouped into slides (up to 2 lines per slide or until the approximate character budget is met) using style "lyrics" and a fixed church caption.

    Note:
        - This function does not validate that the file is a real Bible reference.
          It only checks header patterns and then formats accordingly.
        - The caption format in structured mode follows the current implementation
          (e.g., ``<book> <chapter>장 <verse>절``).

    Args:
        file_path (str):
            Path to the :py:data:`core.config.paths.VERSE_FILE` to parse.
        max_chars (int, optional):
            Maximum character width used when wrapping long verse text or when
            grouping fallback message lines. Defaults to 60. (See also :py:data:`core.config.constants.MAX_CHARS`.)

    Returns:
        list[dict]:
            List of slide dictionaries. Each slide dict contains:

            - "style": "verse" (structured) or "lyrics" (fallback)
            - "caption": caption string
            - "headline": display text (possibly multi-line in fallback mode)
    """
    import re
    import textwrap

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()

    if not lines:
        return []

    header_line = lines[-1]         # Reference or metadata line
    body_lines = lines[:-1]         # Actual verse content

    # Try to match structured formats
    m1 = re.match(r"\((.+?)\s+(\d+)장", header_line)               # Multi-verse format
    m2 = re.match(r"\((.+?)\s+(\d+):(\d+),", header_line)         # Single-verse format

    if m1:
        book, chapter = m1.groups()
    elif m2:
        book, chapter, _ = m2.groups()
    else:
        book = chapter = None

    slides = []

    if book and chapter:
        # ─── Structured Bible verse formatting ───
        for line in body_lines:
            m = re.match(r"(\d+)\s+\u25CB?(.*)", line.strip())  # Match '1 ○text' or '1 text'
            if m:
                verse_num, verse_text = m.groups()
                caption = f"{book} {chapter}장 {verse_num}절"
            else:
                caption = f"{book} {chapter}장"
                verse_text = line.strip()

            chunks = textwrap.wrap(verse_text.strip(), max_chars)
            for chunk in chunks:
                slides.append({
                    "style": "verse",
                    "caption": caption,
                    "headline": chunk
                })
    else:
        # ─── Fallback for unstructured emergency messages ───
        fallback_text = "\n".join(lines).strip()
        raw_lines = fallback_text.splitlines()
        buffer = []
        char_count = 0

        for line in raw_lines:
            line = line.strip()
            if not line:
                continue

            buffer.append(line)
            char_count += len(line)

            # Group 2 lines or if character length exceeded
            if len(buffer) == 2 or char_count >= max_chars:
                slides.append({
                    "style": "lyrics",
                    "caption": "대한예수교장로회(통합) 을지로교회",
                    "headline": "\n".join(buffer)
                })
                buffer = []
                char_count = 0

        if buffer:
            slides.append({
                "style": "lyrics",
                "caption": "대한예수교장로회(통합) 을지로교회",
                "headline": "\n".join(buffer)
            })

    return slides

def backup_slide_if_not_emergency():
    """
    Create a backup copy of the current slide JSON file if no backup exists yet.

    This function writes :py:data:`core.config.paths.SLIDE_BACKUP_FILE` only when that file does not
    already exist. The source is :py:data:`core.config.paths.SLIDE_FILE` if it exists and can be read.

    The backup is intended to support restoration after an emergency subtitle
    session ends. The current implementation skips backup if the loaded slides
    contain any slide whose "style" equals "verse_interrupt".

    Returns:
        None
    """
    if not os.path.exists(paths.SLIDE_BACKUP_FILE):
        try:
            if os.path.exists(paths.SLIDE_FILE):
                with open(paths.SLIDE_FILE, "r", encoding="utf-8") as f:
                    current_slides = json.load(f)
                if all(s.get("style") != "verse_interrupt" for s in current_slides):
                    with open(paths.SLIDE_BACKUP_FILE, "w", encoding="utf-8") as f:
                        json.dump(current_slides, f, ensure_ascii=False, indent=2)
                    print("[✓] 일반 자막 백업 완료")
        except Exception as e:
            print(f"[!] 백업 실패: {e}")

def save_slides(slides, path):
    """
    Save a list of slide dictionaries to a JSON file.

    Args:
        slides (list[dict]):
            Slide dictionaries to write.
        path (str):
            Destination JSON file path (typically :py:data:`core.config.paths.SLIDE_FILE`).

    Returns:
        None
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(slides, f, ensure_ascii=False, indent=2)

class VerseFileHandler(FileSystemEventHandler):
    """
    Watchdog event handler for updates to :py:data:`core.config.paths.VERSE_FILE`.

    This handler listens for filesystem modification events and, when the target
    file is modified, parses it into slides and writes the resulting JSON to
    :py:data:`core.config.paths.SLIDE_FILE`. If slides are generated, it attempts to create a backup
    via :func:`controller.helper.verse_interruptor.backup_slide_if_not_emergency` before overwriting the slide file.
    """

    def on_modified(self, event):
        """
        Handle `watchdog <https://pypi.org/project/watchdog/>`_ "modified" events for :py:data:`core.config.paths.VERSE_FILE`.

        If the modified path matches the target :py:data:`core.config.paths.VERSE_FILE`, this callback:

        1) Parses :py:data:`core.config.paths.VERSE_FILE` into slide dictionaries.

        2) If any slides were produced:

            - Creates a backup (if applicable)
            - Writes slides to :py:data:`core.config.paths.SLIDE_FILE`

        3) Otherwise logs that no slides were generated.

        Args:
            event (FileSystemEvent):
                `Watchdog <https://pypi.org/project/watchdog/>`_ event object describing the filesystem change.

        Returns:
            None
        """
        if event.src_path.endswith(paths.VERSE_FILE):
            print("[INFO] verse_output.txt changed. Parsing...")
            slides = parse_verse_output(paths.VERSE_FILE, constants.MAX_CHARS)

            if slides:
                backup_slide_if_not_emergency()
                save_slides(slides, paths.SLIDE_FILE)
                print(f"[INFO] Saved {len(slides)} slide(s) to {paths.SLIDE_FILE}")
            else:
                print("[WARN] No slides generated.")

def start_interruptor():
    """
    Start the `watchdog <https://pypi.org/project/watchdog/>`_ observer loop for :py:data:`core.config.paths.VERSE_FILE`.

    This sets up an Observer to watch :py:data:`core.config.paths.BASE_DIR` (non-recursive) and uses
    :class:`controller.helper.verse_interruptor.VerseFileHandler` to react to modifications. The function then blocks the
    main thread in a sleep loop until interrupted (Ctrl+C).

    Returns:
        None
    """
    print(f"[DEBUG] Watching directory: {paths.BASE_DIR}")

    observer = Observer()
    handler = VerseFileHandler()
    observer.schedule(handler, paths.BASE_DIR, recursive=False)
    observer.start()
    print("[READY] Watching for verse_output.txt changes... Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[EXIT] Interruptor stopped.")
    observer.join()

if __name__ == "__main__":
    start_interruptor()