# -*- coding: utf-8 -*-
"""
Helpers for extracting first-service worship-order entries from HWPX bulletins.

This module parses HWPX section XML files, locates the portion of the bulletin
that contains the first worship-service order, and converts recognized rows
into normalized dictionaries for generator-side update logic.
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
    r"(?:다같이|인도자|설교자|앉아서|[가-힣A-Za-z·]+(?:목사|장로|집사|권사))+$"
)


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
            "leader": payload,
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
