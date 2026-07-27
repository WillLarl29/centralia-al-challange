from pathlib import Path

from .base import BaseLoader
from .csv_loader import CsvLoader
from .docx_loader import DocxLoader
from .html_loader import HtmlLoader
from .json_loader import JsonLoader
from .markdown_loader import MarkdownLoader
from .pdf_loader import PdfLoader
from .pptx_loader import PptxLoader
from .xlsx_loader import XlsxLoader

_LOADERS_BY_EXTENSION: dict[str, BaseLoader] = {
    ".pdf": PdfLoader(),
    ".docx": DocxLoader(),
    ".doc": DocxLoader(),
    ".xlsx": XlsxLoader(),
    ".xls": XlsxLoader(),
    ".pptx": PptxLoader(),
    ".ppt": PptxLoader(),
    ".md": MarkdownLoader(),
    ".markdown": MarkdownLoader(),
    ".csv": CsvLoader(),
    ".json": JsonLoader(),
    ".html": HtmlLoader(),
    ".htm": HtmlLoader(),
}

SUPPORTED_EXTENSIONS = set(_LOADERS_BY_EXTENSION.keys())


def get_loader_for(path: Path) -> BaseLoader | None:
    return _LOADERS_BY_EXTENSION.get(path.suffix.lower())
