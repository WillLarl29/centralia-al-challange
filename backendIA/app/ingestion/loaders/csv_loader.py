from pathlib import Path

import pandas as pd

from .base import BaseLoader, RawDocument


class CsvLoader(BaseLoader):
    def load(self, path: Path) -> list[RawDocument]:
        df = pd.read_csv(path, dtype=str).fillna("")
        documents: list[RawDocument] = []

        for row_index, row in df.iterrows():
            pairs = [f"{col}: {value}" for col, value in row.items() if str(value).strip()]
            if not pairs:
                continue
            documents.append(
                RawDocument(
                    content=" | ".join(pairs),
                    metadata={"source": path.name, "row": int(row_index) + 2, "type": "csv"},
                )
            )
        return documents
