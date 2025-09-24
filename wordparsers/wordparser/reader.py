import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Iterable, Optional, Tuple

from .utils import NAMESPACES, extract_runs_text, iter_table_cells_text


class WordParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.zip = zipfile.ZipFile(filepath)

    def __enter__(self) -> "WordParser":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def list_files(self) -> List[str]:
        return self.zip.namelist()

    def read_xml(self, path: str) -> ET.Element:
        with self.zip.open(path) as f:
            tree = ET.parse(f)
        return tree.getroot()

    def get_text(self) -> str:
        root = self.read_xml("word/document.xml")
        paragraphs: List[str] = []
        for p in root.findall(".//w:p", NAMESPACES):
            txt = extract_runs_text(p, NAMESPACES)
            if txt:
                paragraphs.append(txt)
        return "\n".join(paragraphs)

    def iter_tables(self) -> Iterable[List[List[str]]]:
        """Итерировать по таблицам, возвращая список строк, каждая строка — список ячеек."""
        root = self.read_xml("word/document.xml")
        for tbl in root.findall(".//w:tbl", NAMESPACES):
            yield list(iter_table_cells_text(tbl, NAMESPACES))

    def get_tables(self) -> List[List[List[str]]]:
        return list(self.iter_tables())

    def get_core_properties(self) -> Dict[str, str]:
        props: Dict[str, str] = {}
        try:
            root = self.read_xml("docProps/core.xml")
        except KeyError:
            return props

        mapping = [
            ("dc:title", "title"),
            ("dc:subject", "subject"),
            ("dc:creator", "creator"),
            ("cp:lastModifiedBy", "lastModifiedBy"),
            ("cp:revision", "revision"),
            ("dcterms:created", "created"),
            ("dcterms:modified", "modified"),
            ("dc:description", "description"),
            ("dc:language", "language"),
            ("dc:keywords", "keywords"),
        ]
        for tag, key in mapping:
            el = root.find(f".//{tag}", NAMESPACES)
            if el is not None and (el.text or "" ):
                props[key] = el.text or ""
        return props

    def list_images(self) -> List[str]:
        return [name for name in self.zip.namelist() if name.startswith("word/media/")]

    def read_image(self, name_or_index: Optional[Tuple[str, int]] = None) -> bytes:
        if isinstance(name_or_index, tuple):
            name, index = name_or_index
        else:
            name, index = None, None

        images = self.list_images()
        if not images:
            raise FileNotFoundError("В документе нет изображений")

        if name is not None and name in images:
            target = name
        elif index is not None and 0 <= index < len(images):
            target = images[index]
        else:
            target = images[0]

        with self.zip.open(target) as f:
            return f.read()

    def close(self):
        self.zip.close()
