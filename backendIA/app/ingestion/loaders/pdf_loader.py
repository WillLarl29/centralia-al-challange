from pathlib import Path

from pypdf import PdfReader

from .base import BaseLoader, RawDocument


class PdfLoader(BaseLoader):
    def load(self, path: Path) -> list[RawDocument]:
        reader = PdfReader(str(path))
        documents: list[RawDocument] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            documents.append(
                RawDocument(
                    content=text,
                    metadata={"source": path.name, "page": page_number, "type": "pdf"},
                )
            )
        return documents
