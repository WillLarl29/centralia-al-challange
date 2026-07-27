from pathlib import Path

from .base import BaseLoader, RawDocument


class MarkdownLoader(BaseLoader):
    def load(self, path: Path) -> list[RawDocument]:
        content = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            return []
        return [RawDocument(content=content, metadata={"source": path.name, "type": "markdown"})]
