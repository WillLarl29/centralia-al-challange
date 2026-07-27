from pathlib import Path

from bs4 import BeautifulSoup

from .base import BaseLoader, RawDocument


class HtmlLoader(BaseLoader):
    def load(self, path: Path) -> list[RawDocument]:
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(lines)

        if not content:
            return []

        title = soup.title.string.strip() if soup.title and soup.title.string else path.name
        return [RawDocument(content=content, metadata={"source": path.name, "title": title, "type": "html"})]
