from __future__ import annotations

from typing import Dict, Iterable, List, Optional
import xml.etree.ElementTree as ET

NAMESPACES: Dict[str, str] = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "vt": "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
}


def findall(element: ET.Element, xpath: str, ns: Optional[Dict[str, str]] = None) -> List[ET.Element]:
    return list(element.findall(xpath, ns or NAMESPACES))


def find(element: ET.Element, xpath: str, ns: Optional[Dict[str, str]] = None) -> Optional[ET.Element]:
    """Безопасный find с дефолтными пространствами имён."""
    return element.find(xpath, ns or NAMESPACES)


def text_or_default(element: Optional[ET.Element], default: str = "") -> str:
    """Вернуть .text элемента или значение по умолчанию."""
    if element is None or element.text is None:
        return default
    return element.text


def extract_runs_text(paragraph: ET.Element, ns: Optional[Dict[str, str]] = None) -> str:
    """Извлечь текст из параграфа, объединяя все w:t внутри w:r."""
    namespaces = ns or NAMESPACES
    texts: List[str] = []
    for t in paragraph.findall(".//w:t", namespaces):
        if t.text:
            texts.append(t.text)
    return "".join(texts)


def element_full_text(element: ET.Element, ns: Optional[Dict[str, str]] = None) -> str:
    """Рекурсивно извлечь видимый текст из узла (параграфы, таблицы, ячейки)."""
    namespaces = ns or NAMESPACES
    parts: List[str] = []

    # Параграфы
    for p in element.findall(".//w:p", namespaces):
        txt = extract_runs_text(p, namespaces)
        if txt:
            parts.append(txt)

    return "\n".join(parts)


def iter_table_cells_text(tbl: ET.Element, ns: Optional[Dict[str, str]] = None) -> Iterable[List[str]]:
    """Итерировать по строкам таблицы, возвращая список текстов по ячейкам."""
    namespaces = ns or NAMESPACES
    for tr in tbl.findall(".//w:tr", namespaces):
        row: List[str] = []
        for tc in tr.findall(".//w:tc", namespaces):
            cell_text_parts: List[str] = []
            for p in tc.findall(".//w:p", namespaces):
                t = extract_runs_text(p, namespaces)
                if t:
                    cell_text_parts.append(t)
            row.append("\n".join(cell_text_parts).strip())
        yield row
