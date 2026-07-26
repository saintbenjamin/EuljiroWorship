# -*- coding: utf-8 -*-
"""
HWPX parsers for the Danseok Church bulletin workflow.

Danseok bulletins place the Sunday morning order in the first table and place
the afternoon order and church news in the second table.  This module is kept
separate from the Euljiro-specific parsers so changes for one bulletin layout
cannot affect the other.
"""

import re
import zipfile
import xml.etree.ElementTree as ET

from core.generator.utils.text_splitter import split_by_length


def _local_name_danseok(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _normalize_line_danseok(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _paragraph_text_danseok(paragraph: ET.Element) -> str:
    return _normalize_line_danseok(
        "".join(
            node.text or ""
            for node in paragraph.iter()
            if _local_name_danseok(node.tag) == "t"
        )
    )


def _load_table_paragraphs_danseok(hwpx_path: str) -> list[list[str]]:
    tables = []

    with zipfile.ZipFile(hwpx_path) as zf:
        section_names = sorted(
            name
            for name in zf.namelist()
            if re.fullmatch(r"Contents/section\d+\.xml", name)
        )

        for section_name in section_names:
            root = ET.fromstring(zf.read(section_name))
            for table in root.iter():
                if _local_name_danseok(table.tag) != "tbl":
                    continue

                paragraphs = []
                for element in table.iter():
                    if _local_name_danseok(element.tag) != "p":
                        continue
                    text = _paragraph_text_danseok(element)
                    if text:
                        paragraphs.append(text)

                if paragraphs:
                    tables.append(paragraphs)

    return tables


def _find_table_danseok(
    tables: list[list[str]],
    marker: str,
) -> list[str]:
    compact_marker = re.sub(r"\s+", "", marker)
    for paragraphs in tables:
        if any(re.sub(r"\s+", "", line).startswith(compact_marker) for line in paragraphs):
            return paragraphs
    raise ValueError(f"HWPX에서 '{marker}' 표를 찾지 못했습니다.")


def _hymn_number_danseok(text: str) -> int | None:
    match = re.search(r"(\d+)\s*장", text)
    return int(match.group(1)) if match else None


def _responsive_number_danseok(text: str) -> int | None:
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def _parse_scripture_reference_danseok(text: str) -> tuple[str, str]:
    text = re.sub(r"\([^)]*(?:구약|신약|쪽|페이지)[^)]*\)", "", text)
    text = re.sub(r"\s*[–—-]\s*", "-", text)
    display_reference = _normalize_line_danseok(text)
    match = re.fullmatch(
        r"(.+?)\s*(\d+)\s*장\s*(\d+)\s*절"
        r"(?:\s*-\s*(\d+)\s*절?)?",
        display_reference,
    )
    if not match:
        return display_reference, display_reference

    book, chapter, verse_start, verse_end = match.groups()
    lookup_reference = f"{book.strip()} {chapter}:{verse_start}"
    if verse_end:
        lookup_reference += f"-{verse_end}"
    return display_reference, lookup_reference


def _parse_morning_rows_danseok(paragraphs: list[str]) -> list[dict]:
    try:
        start = next(i for i, line in enumerate(paragraphs) if "주일오전예배" in line)
    except StopIteration as exc:
        raise ValueError("HWPX에서 주일오전예배 시작 지점을 찾지 못했습니다.") from exc

    end = next(
        (i for i in range(start + 1, len(paragraphs)) if "성도의 교제" in paragraphs[i]),
        len(paragraphs),
    )
    lines = paragraphs[start + 1:end]
    labels = {
        "입례찬송",
        "예배부름기원",
        "신앙고백",
        "죄의 고백 / 사죄의 은총",
        "성시교독",
        "기도",
        "찬송",
        "말씀",
        "말씀선포",
        "찬송/봉헌",
        "축도",
    }
    rows = []
    index = 0

    while index < len(lines):
        label = lines[index]
        if label not in labels:
            index += 1
            continue

        next_index = index + 1
        while next_index < len(lines) and lines[next_index] not in labels:
            next_index += 1
        rows.append((label, lines[index + 1:next_index]))
        index = next_index

    entries = []
    for label, payload in rows:
        raw = " ".join([label, *payload]).strip()

        if label in {"입례찬송", "찬송"}:
            number = _hymn_number_danseok(" ".join(payload))
            if number is not None:
                entries.append({"kind": "hymn", "number": number, "raw": raw})
        elif label == "예배부름기원":
            entries.extend([
                {"kind": "call_to_worship", "raw": raw},
                {"kind": "invocation", "raw": raw},
            ])
        elif label == "신앙고백":
            entries.append({"kind": "creed", "raw": raw})
        elif label == "죄의 고백 / 사죄의 은총":
            entries.append({"kind": "confession_prayer", "raw": raw})
        elif label == "성시교독":
            number = _responsive_number_danseok(" ".join(payload))
            if number is not None:
                entries.append({"kind": "respo", "number": number, "raw": raw})
        elif label == "기도":
            leader = payload[0] if payload else ""
            entries.append({"kind": "prayer", "leader": leader, "raw": raw})
        elif label == "말씀":
            display_reference, lookup_reference = _parse_scripture_reference_danseok(
                payload[0] if payload else ""
            )
            if lookup_reference:
                entries.append({
                    "kind": "verse",
                    "reference": lookup_reference,
                    "display_reference": display_reference,
                    "raw": raw,
                })
        elif label == "말씀선포":
            title_parts = [
                part for part in payload
                if not re.search(r"(?:목사|전도사|강도사)\s*$", part)
                and not re.fullmatch(r"[가-힣]{2,4}", part)
            ]
            title = "\n".join(title_parts).strip()
            preacher = payload[-1] if payload else ""
            entries.append({
                "kind": "sermon",
                "title": title,
                "preacher": preacher,
                "raw": raw,
            })
        elif label == "찬송/봉헌":
            number = _hymn_number_danseok(" ".join(payload))
            if number is not None:
                entries.append({"kind": "hymn", "number": number, "raw": raw})
            entries.append({"kind": "offering", "raw": raw})
        elif label == "축도":
            entries.append({"kind": "benediction", "raw": raw})

    return entries


def extract_first_service_order_entries_from_hwpx_danseok(hwpx_path: str) -> list[dict]:
    tables = _load_table_paragraphs_danseok(hwpx_path)
    paragraphs = _find_table_danseok(tables, "주일오전예배")
    entries = _parse_morning_rows_danseok(paragraphs)
    if not entries:
        raise ValueError("HWPX에서 단석교회 주일오전예배 순서를 파싱하지 못했습니다.")
    return entries


def _format_announcement_headline_danseok(paragraphs: list[str], wrap_width: int) -> str:
    formatted = []
    for paragraph in paragraphs:
        wrapped = split_by_length(paragraph, max_chars=wrap_width) or [paragraph]
        formatted.append("\n".join(wrapped))
    return "\n\n".join(formatted)


def extract_announcement_slides_from_hwpx_danseok(
    hwpx_path: str,
    wrap_width: int = 28,
) -> list[dict]:
    tables = _load_table_paragraphs_danseok(hwpx_path)
    paragraphs = _find_table_danseok(tables, "교회소식")
    start = next(i for i, line in enumerate(paragraphs) if "교회소식" in line) + 1
    end = next(
        (
            i for i in range(start, len(paragraphs))
            if paragraphs[i].startswith("봉헌")
        ),
        len(paragraphs),
    )

    news_lines = [
        _normalize_line_danseok(line)
        for line in paragraphs[start:end]
        if _normalize_line_danseok(line)
        and "진심으로 환영합니다" not in _normalize_line_danseok(line)
    ]
    entries = []
    current = None

    for line in news_lines:
        match = re.match(r"^(\d+)\.\s*(.*)$", line)
        if match:
            if current:
                entries.append(current)
            current = {
                "number": int(match.group(1)),
                "paragraphs": [match.group(2).strip()] if match.group(2).strip() else [],
            }
        elif current:
            current["paragraphs"].append(line)

    if current:
        entries.append(current)

    slides = []
    for entry in entries:
        paragraphs = entry["paragraphs"]
        if not paragraphs:
            continue
        first = paragraphs[0]
        caption_text = first.split(":", 1)[0].strip()
        if len(caption_text) > 24:
            caption_text = f"교회소식 {entry['number']}"
        slides.append({
            "style": "lyrics",
            "caption": caption_text or f"교회소식 {entry['number']}",
            "headline": _format_announcement_headline_danseok(paragraphs, wrap_width),
        })

    if not slides:
        raise ValueError("HWPX에서 단석교회 광고 항목을 추출하지 못했습니다.")
    return slides
