# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/generator/utils/hwpx_worship_order_parser.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

HWPX worship-order parser for the Slide Generator's Euljiro-specific bulletin workflow.

This module parses HWPX section XML files, locates the portions of the weekly
bulletin that contain the first-service worship order and the afternoon praise
service order, and converts supported rows into normalized entry dictionaries
for generator-side update logic.

The logic here is intentionally church-specific. It assumes Euljiro
Presbyterian Church bulletin patterns such as:

- A first-service order embedded in a known HWPX bulletin structure
- An afternoon praise-service order embedded in the second-page middle column
- Worship-order labels and line formats used by Euljiro weekly bulletins
- Euljiro-specific expectations around choir naming, sermon-title handling,
  first-service extraction, praise-service extraction, and special liturgical
  insertions

These helpers exist to support the church-specific Tools-menu import features,
not as a general-purpose HWPX worship-order parser for arbitrary churches.
"""

import re
import zipfile
import xml.etree.ElementTree as ET

CHOIR_NAMES = (
    "시온찬양대",
    "할렐루야찬양대",
    "마리아찬양대",
    "갈렙찬양대",
    "연합찬양대",
    "찬양대",
)

ROLE_SUFFIX_RE = re.compile(
    r"(?:다같이|인도자|설교자|앉아서|[가-힣A-Za-z·0-9()]+(?:목사|장로|집사|권사))+$"
)

PRAISE_SERVICE_START_MARKER = "오후2:30인도:"
PRAISE_SERVICE_END_MARKERS = (
    "*다음주",
    "영유아유치부",
    "오후12:00인도:",
)
PRAISE_SERVICE_TOKENS = (
    "전주반주자",
    "기원인도자",
    "성경봉독",
    "봉헌기도",
    "교회소식",
    "사업보고",
    "찬송",
    "기도",
    "찬양",
    "말씀",
    "봉헌",
    "인사",
    "축도",
)
PRAISE_SERVICE_NEXT_MARKERS = {
    "__leader__": (
        "전주반주자",
        "기원인도자",
        "찬송",
        "기도",
        "성경봉독",
        "찬양",
        "말씀",
    ),
    "전주반주자": (
        "기원인도자",
        "찬송",
        "기도",
    ),
    "기원인도자": (
        "찬송",
        "기도",
        "성경봉독",
    ),
    "찬송": (
        "기도",
        "성경봉독",
        "찬양",
        "교회소식",
        "봉헌기도",
        "봉헌",
        "축도",
        "인사",
        "사업보고",
    ),
    "기도": (
        "찬송",
        "성경봉독",
        "찬양",
        "교회소식",
        "봉헌기도",
        "봉헌",
        "축도",
        "인사",
        "사업보고",
    ),
    "성경봉독": (
        "찬양",
        "말씀",
    ),
    "찬양": (
        "말씀",
        "교회소식",
        "봉헌기도",
        "봉헌",
        "축도",
        "인사",
        "사업보고",
        "찬송",
    ),
    "말씀": (
        "기도",
        "봉헌기도",
        "봉헌",
        "교회소식",
        "찬송",
        "축도",
        "인사",
        "사업보고",
    ),
    "봉헌": (
        "봉헌기도",
        "인사",
        "사업보고",
        "교회소식",
        "찬송",
        "축도",
    ),
    "봉헌기도": (
        "인사",
        "사업보고",
        "교회소식",
        "찬송",
        "축도",
    ),
    "인사": (
        "사업보고",
        "교회소식",
        "찬송",
        "축도",
    ),
    "사업보고": (
        "교회소식",
        "찬송",
        "축도",
    ),
    "교회소식": (
        "찬송",
        "축도",
    ),
    "축도": (),
}


def _local_name(tag: str) -> str:
    """
    Return the local XML tag name without namespace or prefix information.

    Args:
        tag (str):
            Raw XML tag string, optionally including a namespace URI or prefix.

    Returns:
        str:
            Local tag name stripped of namespace wrappers and prefixes.
    """
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    if ":" in tag:
        return tag.rsplit(":", 1)[-1]
    return tag


def _normalize_line(text: str) -> str:
    """
    Normalize a paragraph line into a compact single-line string.

    Args:
        text (str):
            Raw paragraph text extracted from the HWPX XML tree.

    Returns:
        str:
            Trimmed text with consecutive whitespace collapsed to single spaces.
    """
    return " ".join((text or "").replace("\r", "\n").split()).strip()


def _compact(text: str) -> str:
    """
    Remove all whitespace from a string for loose structural comparisons.

    Args:
        text (str):
            Source text to compact.

    Returns:
        str:
            Text with all whitespace removed.
    """
    return re.sub(r"\s+", "", text or "")


def _strip_role_suffix(text: str) -> str:
    """
    Remove known liturgical role suffixes from a parsed order fragment.

    Args:
        text (str):
            Raw title or reference text that may end with role labels such as
            preacher or leader names.

    Returns:
        str:
            Cleaned text with recognized role suffixes removed.
    """
    return ROLE_SUFFIX_RE.sub("", text).strip()


def _space_person_role_suffix(text: str) -> str:
    """
    Insert a single display-friendly space before a trailing role suffix.

    Args:
        text (str):
            Person-like text that may end with a role such as ``목사``,
            ``장로``, ``집사``, ``권사``, or ``전도사``.

    Returns:
        str:
            Text with a single space inserted before the trailing role suffix
            when one is detected. Existing spacing is preserved.
        """
    text = _normalize_line(text)
    if not text:
        return text

    return re.sub(
        r"(?<!\s)(목사|장로|집사|권사|전도사)(\s*\([^)]*\))?$",
        r" \1\2",
        text,
    )


def _load_section_paragraphs(hwpx_path: str) -> list[str]:
    """
    Read all section XML files in a HWPX archive and collect paragraph text.

    Args:
        hwpx_path (str):
            Filesystem path to the source HWPX bulletin file.

    Returns:
        list[str]:
            Normalized paragraph strings gathered from the section XML files in
            document order.
    """
    with zipfile.ZipFile(hwpx_path) as zf:
        section_names = sorted(
            name for name in zf.namelist()
            if name.lower().endswith(".xml") and "section" in name.lower()
        )

        paragraphs = []
        for name in section_names:
            root = ET.fromstring(zf.read(name))
            for elem in root.iter():
                if _local_name(elem.tag) not in {"p", "paragraph"}:
                    continue

                text = _normalize_line("".join(elem.itertext()))
                if text:
                    paragraphs.append(text)

        return paragraphs


def _extract_first_service_lines(paragraphs: list[str]) -> list[str]:
    """
    Slice the paragraph list down to the first-service worship-order region.

    The extracted range starts at the first line containing the entrance hymn
    marker and stops before the ``성도의교제`` section, which is handled
    separately as the announcement block.

    Args:
        paragraphs (list[str]):
            Full paragraph stream extracted from the HWPX bulletin.

    Returns:
        list[str]:
            Paragraph subset representing the first-service worship order.

    Raises:
        ValueError:
            Raised when either the start or end anchor cannot be found.
    """
    start_idx = None
    end_idx = None

    for i, line in enumerate(paragraphs):
        compact = _compact(line)
        if start_idx is None and "입례찬송" in compact:
            start_idx = i
            continue

        if start_idx is not None and "성도의교제" in compact:
            end_idx = i
            break

    if start_idx is None:
        raise ValueError("HWPX에서 1부 예배순서 시작 지점을 찾지 못했습니다.")

    if end_idx is None:
        raise ValueError("HWPX에서 성도의교제 지점을 찾지 못했습니다.")

    return paragraphs[start_idx:end_idx]


def _compact_with_index_map(text: str) -> tuple[str, list[int]]:
    """
    Compact a string while preserving a reverse index map to the original text.

    Args:
        text (str):
            Source text that may contain whitespace between meaningful tokens.

    Returns:
        tuple[str, list[int]]:
            Two-element tuple containing the whitespace-free text and a list
            mapping each compacted character index back to the original string
            index.
    """
    compact_chars = []
    index_map = []

    for index, char in enumerate(text):
        if char.isspace():
            continue
        compact_chars.append(char)
        index_map.append(index)

    return "".join(compact_chars), index_map


def _slice_by_compact_range(
    text: str,
    index_map: list[int],
    start_index: int,
    end_index: int,
) -> str:
    """
    Slice the original text using a range expressed in compacted-text indices.

    Args:
        text (str):
            Original un-compacted text.
        index_map (list[int]):
            Index map returned by :func:`_compact_with_index_map`.
        start_index (int):
            Inclusive compact-text start index.
        end_index (int):
            Exclusive compact-text end index.

    Returns:
        str:
            Original-text substring that spans the requested compact-text
            range. Returns an empty string when the requested range is empty.
    """
    if not index_map or end_index <= start_index:
        return ""

    start_index = max(start_index, 0)
    end_index = min(end_index, len(index_map))
    if end_index <= start_index:
        return ""

    original_start = index_map[start_index]
    original_end = index_map[end_index - 1] + 1
    return text[original_start:original_end]


def _find_next_marker(
    compact_text: str,
    start_index: int,
    markers: tuple[str, ...],
) -> int:
    """
    Find the earliest marker occurrence at or after the given compact index.

    Args:
        compact_text (str):
            Whitespace-free comparison text.
        start_index (int):
            Compact-text index from which the search should begin.
        markers (tuple[str, ...]):
            Marker strings to search for.

    Returns:
        int:
            Earliest matching compact-text index, or ``-1`` if no marker is
            found.
    """
    candidates = []

    for marker in markers:
        position = compact_text.find(marker, start_index)
        if position != -1:
            candidates.append(position)

    return min(candidates) if candidates else -1


def _extract_praise_service_segment(paragraphs: list[str]) -> str:
    """
    Extract the afternoon praise-service order segment from the bulletin.

    The Euljiro weekly bulletin usually stores the afternoon praise-service
    order as a compact middle-column text run on the second page. This helper
    finds the known afternoon-service start marker, then trims the segment
    before the next unrelated schedule section.

    Args:
        paragraphs (list[str]):
            Full paragraph stream extracted from the HWPX bulletin.

    Returns:
        str:
            Original-text segment that contains only the afternoon
            praise-service order.

    Raises:
        ValueError:
            Raised when the afternoon praise-service segment cannot be located.
    """
    joined_text = " ".join(paragraphs)
    compact_text, index_map = _compact_with_index_map(joined_text)

    start_index = compact_text.find(PRAISE_SERVICE_START_MARKER)
    if start_index == -1:
        raise ValueError("HWPX에서 오후찬양예배 순서 시작 지점을 찾지 못했습니다.")

    end_index = _find_next_marker(
        compact_text,
        start_index + len(PRAISE_SERVICE_START_MARKER),
        PRAISE_SERVICE_END_MARKERS,
    )
    if end_index == -1:
        end_index = len(compact_text)

    segment = _slice_by_compact_range(joined_text, index_map, start_index, end_index)
    if not segment.strip():
        raise ValueError("HWPX에서 오후찬양예배 순서 본문을 추출하지 못했습니다.")

    return segment


def _clean_praise_service_payload(text: str) -> str:
    """
    Normalize a raw afternoon-service payload fragment for display and parsing.

    Args:
        text (str):
            Raw substring captured between afternoon-service order markers.

    Returns:
        str:
            Cleaned text with decorative ellipsis separators removed and
            whitespace normalized.
    """
    text = _normalize_line(text)
    text = re.sub(r"[.…⋯]{2,}", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" :-")

    compact_text = _compact(text)
    if compact_text in {"다같이", "인도자", "설교자", "반주자", "찬양대", "중창단"}:
        return compact_text

    return text


def _split_numbered_people_entries(text: str) -> list[str]:
    """
    Split numbered person lists such as ``①안재평 목사②김용옥 장로``.

    Args:
        text (str):
            Raw numbered list payload extracted from an ``인사`` block.

    Returns:
        list[str]:
            Individual person-entry strings. Returns the original text as a
            single-item list when no numbered sub-entries are detected.
    """
    cleaned = _clean_praise_service_payload(text)
    if not cleaned:
        return []

    if not re.search(r"[①②③④⑤⑥⑦⑧⑨]", cleaned):
        return [cleaned]

    parts = re.split(r"[①②③④⑤⑥⑦⑧⑨]\s*", cleaned)
    return [part.strip() for part in parts if part.strip()]


def _parse_praise_service_token(token: str, payload: str, raw: str) -> list[dict]:
    """
    Convert one afternoon-service token and payload into normalized entries.

    Args:
        token (str):
            Compact service-order token that identified the current block.
        payload (str):
            Normalized payload text following the token.
        raw (str):
            Original raw payload substring captured from the bulletin segment.

    Returns:
        list[dict]:
            One or more normalized entry dictionaries representing the parsed
            token block.
    """
    if token == "전주반주자":
        return [{
            "kind": "prelude",
            "leader": "반주자",
            "raw": raw,
        }]

    if token == "기원인도자":
        return [{
            "kind": "invocation",
            "leader": "인도자",
            "raw": raw,
        }]

    if token == "찬송":
        number_match = re.search(r"(\d+)장", _compact(payload))
        if not number_match:
            return []
        return [{
            "kind": "hymn",
            "number": int(number_match.group(1)),
            "raw": raw,
        }]

    if token == "기도":
        compact_payload = _compact(payload)
        if "설교자" in compact_payload:
            return [{
                "kind": "post_sermon_prayer",
                "raw": raw,
            }]

        return [{
            "kind": "prayer",
            "leader": _space_person_role_suffix(payload),
            "raw": raw,
        }]

    if token == "성경봉독":
        compact_payload = _compact(payload)
        reference_match = re.match(r"(.+?\d+:\d+(?:-\d+)?)", compact_payload)
        return [{
            "kind": "verse",
            "reference": (
                reference_match.group(1)
                if reference_match
                else _strip_role_suffix(compact_payload)
            ),
            "raw": raw,
        }]

    if token == "찬양":
        compact_payload = _compact(payload)
        hymn_match = re.search(r"(\d+)장", compact_payload)
        if hymn_match:
            return [{
                "kind": "hymn",
                "number": int(hymn_match.group(1)),
                "raw": raw,
            }]

        return [{
            "kind": "special_praise",
            "group": payload,
            "raw": raw,
        }]

    if token == "말씀":
        return [{
            "kind": "sermon",
            "title": payload,
            "preacher": "",
            "raw": raw,
        }]

    if token == "봉헌":
        return [{
            "kind": "offering",
            "text": payload or "다같이",
            "raw": raw,
        }]

    if token == "봉헌기도":
        return [{
            "kind": "offering_prayer",
            "leader": _space_person_role_suffix(payload),
            "raw": raw,
        }]

    if token == "인사":
        return [
            {
                "kind": "greeting",
                "person": _space_person_role_suffix(person),
                "raw": raw,
            }
            for person in _split_numbered_people_entries(payload)
        ]

    if token == "사업보고":
        return [{
            "kind": "report",
            "text": payload,
            "raw": raw,
        }]

    if token == "교회소식":
        return [{
            "kind": "church_news",
            "leader": _space_person_role_suffix(payload or "인도자"),
            "raw": raw,
        }]

    if token == "축도":
        return [{
            "kind": "benediction",
            "leader": _space_person_role_suffix(payload),
            "raw": raw,
        }]

    return []


def _parse_praise_service_segment(segment: str) -> list[dict]:
    """
    Parse the extracted afternoon praise-service segment into entry dictionaries.

    Args:
        segment (str):
            Afternoon praise-service source text extracted from the bulletin.

    Returns:
        list[dict]:
            Ordered list of normalized afternoon-service entry dictionaries.
    """
    compact_text, index_map = _compact_with_index_map(segment)
    start_index = compact_text.find(PRAISE_SERVICE_START_MARKER)
    if start_index == -1:
        return []

    entries = []
    cursor = start_index + len(PRAISE_SERVICE_START_MARKER)

    next_marker = _find_next_marker(
        compact_text,
        cursor,
        PRAISE_SERVICE_NEXT_MARKERS["__leader__"],
    )
    if next_marker == -1:
        next_marker = len(compact_text)

    leader_raw = _slice_by_compact_range(segment, index_map, cursor, next_marker)
    leader = _space_person_role_suffix(_clean_praise_service_payload(leader_raw))
    if leader:
        entries.append({
            "kind": "service_leader",
            "leader": leader,
            "raw": leader_raw,
        })

    cursor = next_marker

    while cursor < len(compact_text):
        token = next(
            (candidate for candidate in PRAISE_SERVICE_TOKENS if compact_text.startswith(candidate, cursor)),
            None,
        )
        if token is None:
            next_cursor = _find_next_marker(compact_text, cursor + 1, PRAISE_SERVICE_TOKENS)
            if next_cursor == -1:
                break
            cursor = next_cursor
            continue

        payload_start = cursor + len(token)
        next_markers = PRAISE_SERVICE_NEXT_MARKERS.get(token, PRAISE_SERVICE_TOKENS)
        next_cursor = _find_next_marker(compact_text, payload_start, next_markers)
        if next_cursor == -1:
            next_cursor = len(compact_text)

        payload_raw = _slice_by_compact_range(segment, index_map, payload_start, next_cursor)
        payload = _clean_praise_service_payload(payload_raw)

        entries.extend(_parse_praise_service_token(token, payload, payload_raw))
        cursor = next_cursor

    return [entry for entry in entries if entry]


def _parse_order_line(line: str) -> dict | None:
    """
    Parse a single worship-order line into a normalized entry dictionary.

    Sermon lines are handled conservatively: the payload after ``말씀선포`` is
    preserved as-is rather than aggressively split into title and preacher
    segments, because many HWPX exports collapse those boundaries unreliably.

    Args:
        line (str):
            One normalized bulletin line from the first-service order region.

    Returns:
        dict | None:
            Parsed entry dictionary containing a ``kind`` key and any
            kind-specific metadata, or ``None`` when the line is not recognized
            as a supported worship-order item. For sermon entries, the
            ``title`` field may intentionally include a glued preacher suffix
            that later generator logic can remove more safely using the
            existing slide context.
    """
    normalized = _normalize_line(line).lstrip("※*").strip()
    compact = _compact(normalized)

    if not compact:
        return None

    if compact.startswith("2부:"):
        return None

    if compact.startswith("다음주") or compact.startswith("(※"):
        return None

    hymn_match = re.search(r"(?:입례찬송|찬송|송영)\s*(\d+)장", compact)
    if hymn_match:
        return {
            "kind": "hymn",
            "number": int(hymn_match.group(1)),
            "raw": line,
        }

    if compact.startswith("성시교독"):
        match = re.search(r"성시교독(\d+)", compact)
        if match:
            return {
                "kind": "respo",
                "number": int(match.group(1)),
                "raw": line,
            }

    if compact.startswith("성경봉독"):
        payload = _strip_role_suffix(compact[len("성경봉독"):])
        return {
            "kind": "verse",
            "reference": payload,
            "raw": line,
        }

    if compact.startswith("찬양1부:"):
        payload_raw = re.sub(r"^\s*찬\s*양\s*1\s*부\s*:\s*", "", normalized).strip()
        compact_payload = _compact(payload_raw)

        choir_name = "찬양대"
        title = payload_raw

        for choir in sorted(CHOIR_NAMES, key=len, reverse=True):
            compact_choir = _compact(choir)
            if not compact_payload.endswith(compact_choir):
                continue

            choir_name = choir

            if payload_raw.endswith(choir):
                title = payload_raw[:-len(choir)].strip()
            else:
                title = compact_payload[:-len(compact_choir)].strip()

            break

        return {
            "kind": "anthem",
            "title": title.strip(),
            "choir": choir_name,
            "raw": line,
        }

    if compact.startswith("말씀선포"):
        payload_raw = re.sub(r"^\s*말\s*씀\s*선\s*포\s*", "", normalized).strip()

        # Preserve the sermon payload verbatim.
        # Do not try to guess the preacher here, because HWPX often collapses
        # the sermon title and preacher name together without a reliable boundary.
        return {
            "kind": "sermon",
            "title": payload_raw,
            "preacher": "",
            "raw": line,
        }

    if compact.startswith("예배의부름"):
        return {"kind": "call_to_worship", "raw": line}

    if compact.startswith("화답송영"):
        return {"kind": "response_doxology", "raw": line}

    if compact.startswith("화답송"):
        return {"kind": "response_song", "raw": line}

    if compact.startswith("기원"):
        return {"kind": "invocation", "raw": line}

    if compact.startswith("신앙고백"):
        return {"kind": "creed", "raw": line}

    if compact.startswith("고백의기도"):
        return {"kind": "confession_prayer", "raw": line}

    if compact.startswith("봉헌기도"):
        return {"kind": "offering_prayer", "raw": line}

    if compact.startswith("봉헌"):
        return {"kind": "offering", "raw": line}

    if compact.startswith("축도"):
        return {"kind": "benediction", "raw": line}

    if compact.startswith("기도"):
        payload = compact[len("기도"):].strip()
        if "설교자" in payload:
            return {"kind": "post_sermon_prayer", "raw": line}
        return {
            "kind": "prayer",
            "leader": _space_person_role_suffix(payload),
            "raw": line,
        }

    if "성찬식" in compact:
        return {"kind": "communion", "raw": line}

    return None

def extract_first_service_order_entries_from_hwpx(hwpx_path: str) -> list[dict]:
    """
    Extract recognized first-service worship-order entries from a HWPX bulletin.

    Args:
        hwpx_path (str):
            Filesystem path to the source HWPX bulletin file.

    Returns:
        list[dict]:
            Ordered list of normalized worship-order entry dictionaries suitable
            for generator-side update logic.

    Raises:
        ValueError:
            Raised when no supported first-service worship-order items can be
            extracted from the file.
    """
    paragraphs = _load_section_paragraphs(hwpx_path)
    service_lines = _extract_first_service_lines(paragraphs)

    entries = []
    seen = set()

    for line in service_lines:
        parsed = _parse_order_line(line)
        if not parsed:
            continue

        dedupe_key = (parsed["kind"], parsed.get("number"), parsed.get("title"), parsed.get("reference"))
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        entries.append(parsed)

    if not entries:
        raise ValueError("HWPX에서 1부 예배순서 항목을 파싱하지 못했습니다.")

    return entries


def extract_praise_service_order_entries_from_hwpx(hwpx_path: str) -> list[dict]:
    """
    Extract recognized afternoon praise-service order entries from a HWPX bulletin.

    Args:
        hwpx_path (str):
            Filesystem path to the source HWPX bulletin file.

    Returns:
        list[dict]:
            Ordered list of normalized afternoon praise-service entry
            dictionaries suitable for generator-side update logic.

    Raises:
        ValueError:
            Raised when no supported afternoon praise-service items can be
            extracted from the file.
    """
    paragraphs = _load_section_paragraphs(hwpx_path)
    segment = _extract_praise_service_segment(paragraphs)
    entries = _parse_praise_service_segment(segment)

    if not entries:
        raise ValueError("HWPX에서 오후찬양예배 순서 항목을 파싱하지 못했습니다.")

    return entries
