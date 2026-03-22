# -*- coding: utf-8 -*-

import re
import zipfile
import xml.etree.ElementTree as ET

from core.generator.utils.text_splitter import split_by_length

SECTION_NAMES = ("환영", "예배", "모임", "소식")
SECTION_FALLBACK_CAPTIONS = {
    "환영": "성도의 교제",
}

BRACKET_TITLE_RE = re.compile(r"^[\[【]\s*(.+?)\s*[\]】]\s*(.*)$")
BULLET_RE = re.compile(r"^[\-•·ㆍ∙]\s*(.+)$")
WHITESPACE_RE = re.compile(r"[ \t\u00A0\u3000]+")
INLINE_BULLET_SPLIT_RE = re.compile(r"\s+(?=[\-•·ㆍ∙]\s*)")


def _local_name(tag: str) -> str:
    """
    Return the local XML element name without namespace or prefix markers.

    Args:
        tag (str):
            Raw XML tag string, possibly including a namespace URI or prefix.

    Returns:
        str:
            Normalized local tag name.
    """
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    if ":" in tag:
        return tag.rsplit(":", 1)[-1]
    return tag


def _compact(text: str) -> str:
    """
    Remove all whitespace from a text string.

    Args:
        text (str):
            Input text to compact.

    Returns:
        str:
            Text with all whitespace removed.
    """
    return re.sub(r"\s+", "", text or "")


def _normalize_line(text: str) -> str:
    """
    Normalize a single extracted text line for downstream parsing.

    Args:
        text (str):
            Raw text extracted from the HWPX XML.

    Returns:
        str:
            Cleaned line text.
    """
    text = (text or "").replace("\r", "\n").replace("\u200b", "")
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _normalize_for_compare(text: str) -> str:
    """
    Normalize text for loose equality checks between similar entries.

    Args:
        text (str):
            Source text to normalize.

    Returns:
        str:
            Compacted text with comparison-noise characters removed.
    """
    text = _compact(text)
    for ch in "-•·ㆍ∙:()[]{}【】":
        text = text.replace(ch, "")
    return text


def _is_fixed_welcome_line(line: str) -> bool:
    """
    Check whether a line matches the fixed welcome sentence.

    Args:
        line (str):
            Candidate announcement line.

    Returns:
        bool:
            True if the line is the fixed welcome text, otherwise False.
    """
    compact = _normalize_for_compare(line).rstrip(".!")
    return compact == _normalize_for_compare("오늘 처음 오신 분들을 환영하고 축복합니다.")


def _xml_sort_key(name: str):
    """
    Build a stable sort key for XML entries inside a HWPX archive.

    Args:
        name (str):
            Archive entry name.

    Returns:
        tuple:
            Sort key suitable for ordering section XML files before other XML files.
    """
    lower = name.lower()
    match = re.search(r"section(\d+)\.xml$", lower)
    if match:
        return (0, int(match.group(1)), lower)
    return (1, 0, lower)


def _iter_table_paragraph_groups(hwpx_path: str):
    """
    Yield paragraph lists extracted from each table found in a HWPX file.

    Args:
        hwpx_path (str):
            Path to the source ``.hwpx`` file.

    Yields:
        list[str]:
            Paragraph texts collected from a single table element.
    """
    with zipfile.ZipFile(hwpx_path) as zf:
        xml_names = sorted(
            [name for name in zf.namelist() if name.lower().endswith(".xml")],
            key=_xml_sort_key
        )

        for name in xml_names:
            try:
                root = ET.fromstring(zf.read(name))
            except ET.ParseError:
                continue

            for elem in root.iter():
                if _local_name(elem.tag) not in {"tbl", "table"}:
                    continue

                paragraphs = []
                last_text = None

                for para in elem.iter():
                    if _local_name(para.tag) not in {"p", "paragraph"}:
                        continue

                    text = _normalize_line("".join(para.itertext()))
                    if text and text != last_text:
                        paragraphs.append(text)
                        last_text = text

                if paragraphs:
                    yield paragraphs


def _score_table(paragraphs: list[str]) -> int:
    """
    Score a table candidate based on how closely it resembles an announcement block.

    Args:
        paragraphs (list[str]):
            Paragraph texts extracted from a single table.

    Returns:
        int:
            Heuristic score where higher values indicate a more likely
            announcement table.
    """
    compact_lines = [_compact(line).lstrip("∙•·ㆍ-") for line in paragraphs]
    section_hits = sum(
        1 for name in SECTION_NAMES
        if any(line == name for line in compact_lines)
    )
    bracket_hits = sum(1 for line in paragraphs if BRACKET_TITLE_RE.match(line))

    score = (section_hits * 100) + (bracket_hits * 5) + min(len(paragraphs), 40)

    if any(_is_fixed_welcome_line(line) for line in paragraphs):
        score += 40

    if any("창립70주년기념사업" in _compact(line) for line in paragraphs):
        score += 10

    return score


def _select_announcement_paragraphs(hwpx_path: str) -> list[str]:
    """
    Select the most likely announcement table from a HWPX bulletin.

    Args:
        hwpx_path (str):
            Path to the source `.hwpx` file.

    Returns:
        list[str]:
            Paragraph texts from the best matching announcement table.

    Raises:
        ValueError:
            Raised when no sufficiently strong announcement-table candidate is found.
    """
    best_paragraphs = []
    best_score = -1

    for paragraphs in _iter_table_paragraph_groups(hwpx_path):
        score = _score_table(paragraphs)
        if score > best_score:
            best_score = score
            best_paragraphs = paragraphs

    if not best_paragraphs or best_score < 100:
        raise ValueError("광고 표를 찾지 못했습니다. 실제 HWPX 구조에 맞춰 파서를 조금 조정해야 합니다.")

    return best_paragraphs


def _detect_section(line: str) -> str | None:
    """
    Detect whether a line is one of the known announcement section headers.

    Args:
        line (str):
            Normalized line text.

    Returns:
        str | None:
            Matching section name, or `None` if the line is not a section header.
    """
    compact = _compact(line).lstrip("∙•·ㆍ-")
    for section in SECTION_NAMES:
        if compact == section:
            return section
    return None


def _split_inline_bullets(text: str) -> list[str]:
    """
    Split a paragraph that contains multiple inline bullet items.

    Args:
        text (str):
            Input paragraph text that may contain inline bullet separators.

    Returns:
        list[str]:
            Individual bullet-like text segments. If no split is possible,
            the original text is returned as a single-element list.
    """
    text = _normalize_line(text)
    if not text:
        return []

    parts = INLINE_BULLET_SPLIT_RE.split(text)
    cleaned = []

    for part in parts:
        part = _normalize_line(part)
        if not part:
            continue
        part = re.sub(r"^[\-•·ㆍ∙]\s*", "", part).strip()
        if part:
            cleaned.append(part)

    return cleaned or [text]


def _format_headline(paragraphs: list[str], wrap_width: int) -> str:
    """
    Format entry paragraphs into a slide-ready multiline headline string.

    Args:
        paragraphs (list[str]):
            Entry body paragraphs to format.
        wrap_width (int):
            Maximum line width used for wrapping.

    Returns:
        str:
            Paragraphs joined into a slide headline with blank lines preserved
            between logical blocks.
    """
    formatted = []

    for para in paragraphs:
        para = _normalize_line(para)
        if not para:
            continue

        wrapped = split_by_length(para, max_chars=wrap_width)
        if not wrapped:
            wrapped = [para]

        formatted.append("\n".join(wrapped))

    return "\n\n".join(formatted)


def _flush_entry(entry: dict | None, entries: list[dict]) -> None:
    """
    Validate the current entry and append it to the parsed entry list.

    Args:
        entry (dict | None):
            Entry currently being accumulated.
        entries (list[dict]):
            Output list that stores parsed entries.

    Returns:
        None
    """
    if not entry:
        return

    caption = _normalize_line(entry.get("caption", ""))
    paragraphs = [_normalize_line(p) for p in entry.get("paragraphs", []) if _normalize_line(p)]

    if not caption or not paragraphs:
        return

    entries.append({
        "caption": caption,
        "paragraphs": paragraphs,
    })


def _entry_score(entry: dict) -> tuple[int, int, int]:
    """
    Compute a richness score used to choose between duplicate caption entries.

    Args:
        entry (dict):
            Parsed announcement entry containing `caption` and `paragraphs`.

    Returns:
        tuple[int, int, int]:
            Comparison tuple where larger values indicate a more informative entry.
    """
    paragraphs = entry.get("paragraphs", [])
    joined = " ".join(paragraphs)
    bullet_like_count = sum(
        1 for p in paragraphs
        if ":" in p or len(_split_inline_bullets(p)) > 1
    )
    return (
        len(paragraphs),
        bullet_like_count,
        len(joined),
    )


def _dedupe_entries(entries: list[dict]) -> list[dict]:
    """
    Remove duplicate parsed entries while preserving the stronger candidate.

    Args:
        entries (list[dict]):
            Parsed announcement entries before deduplication.

    Returns:
        list[dict]:
            Deduplicated entry list.
    """
    deduped = []
    caption_index = {}

    for entry in entries:
        key = _normalize_for_compare(entry["caption"])
        existing_idx = caption_index.get(key)

        if existing_idx is None:
            caption_index[key] = len(deduped)
            deduped.append(entry)
            continue

        existing = deduped[existing_idx]

        existing_text = _normalize_for_compare(" ".join(existing["paragraphs"]))
        incoming_text = _normalize_for_compare(" ".join(entry["paragraphs"]))

        if existing_text == incoming_text:
            continue

        if _entry_score(entry) > _entry_score(existing):
            deduped[existing_idx] = entry

    return deduped


def _parse_announcement_paragraphs(paragraphs: list[str], wrap_width: int) -> list[dict]:
    """
    Parse announcement table paragraphs into generator slide dictionaries.

    Args:
        paragraphs (list[str]):
            Paragraphs extracted from the selected announcement table.
        wrap_width (int):
            Maximum line width used when formatting slide headlines.

    Returns:
        list[dict]:
            Slide dictionaries in generator format. All returned slides use the
            `lyrics` style.
    """
    entries = []
    current_section = None
    current_entry = None

    for raw_line in paragraphs:
        line = _normalize_line(raw_line)
        if not line:
            continue

        section = _detect_section(line)
        if section:
            _flush_entry(current_entry, entries)
            current_entry = None
            current_section = section
            continue

        if current_section is None:
            continue

        if _is_fixed_welcome_line(line):
            continue

        bracket_match = BRACKET_TITLE_RE.match(line)
        if bracket_match:
            _flush_entry(current_entry, entries)

            caption = _normalize_line(bracket_match.group(1))
            rest = _normalize_line(bracket_match.group(2))

            current_entry = {
                "caption": caption,
                "paragraphs": [],
            }

            if rest:
                current_entry["paragraphs"].extend(_split_inline_bullets(rest))

            continue

        bullet_match = BULLET_RE.match(line)
        if bullet_match:
            bullet_text = _normalize_line(bullet_match.group(1))

            if current_entry is None:
                current_entry = {
                    "caption": SECTION_FALLBACK_CAPTIONS.get(current_section, current_section),
                    "paragraphs": [],
                }

            current_entry["paragraphs"].append(bullet_text)
            continue

        if current_entry:
            if current_entry["paragraphs"]:
                current_entry["paragraphs"][-1] = (
                    f"{current_entry['paragraphs'][-1]} {line}"
                ).strip()
            else:
                current_entry["paragraphs"].append(line)
            continue

        current_entry = {
            "caption": SECTION_FALLBACK_CAPTIONS.get(current_section, current_section),
            "paragraphs": [line],
        }

    _flush_entry(current_entry, entries)

    entries = _dedupe_entries(entries)

    slides = []
    for entry in entries:
        slides.append({
            "style": "lyrics",
            "caption": entry["caption"],
            "headline": _format_headline(entry["paragraphs"], wrap_width),
        })

    return slides


def extract_announcement_slides_from_hwpx(hwpx_path: str, wrap_width: int = 28) -> list[dict]:
    """
    Extract announcement slides from a HWPX bulletin file.

    Args:
        hwpx_path (str):
            Path to the source `.hwpx` file.
        wrap_width (int, optional):
            Maximum line width used when wrapping announcement text. Defaults to 28.

    Returns:
        list[dict]:
            Parsed announcement slides in generator format.

    Raises:
        ValueError:
            Raised when no announcement table or announcement entries can be extracted.
    """
    paragraphs = _select_announcement_paragraphs(hwpx_path)
    slides = _parse_announcement_paragraphs(paragraphs, wrap_width)

    if not slides:
        raise ValueError("광고 항목을 추출하지 못했습니다.")

    return slides

