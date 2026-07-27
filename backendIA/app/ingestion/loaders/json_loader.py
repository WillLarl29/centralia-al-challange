import json
from pathlib import Path

from .base import BaseLoader, RawDocument


class JsonLoader(BaseLoader):
    def load(self, path: Path) -> list[RawDocument]:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)

        documents: list[RawDocument] = []

        if isinstance(data, list):
            for index, item in enumerate(data):
                content = self._stringify(item)
                if content:
                    documents.append(
                        RawDocument(
                            content=content,
                            metadata={"source": path.name, "record": index, "type": "json"},
                        )
                    )
        else:
            content = self._stringify(data)
            if content:
                documents.append(RawDocument(content=content, metadata={"source": path.name, "type": "json"}))

        return documents

    @staticmethod
    def _stringify(value) -> str:
        if isinstance(value, dict):
            return " | ".join(f"{k}: {v}" for k, v in value.items() if str(v).strip())
        return json.dumps(value, ensure_ascii=False)
