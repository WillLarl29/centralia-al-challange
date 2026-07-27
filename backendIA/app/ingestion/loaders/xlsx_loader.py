from pathlib import Path

import pandas as pd

from .base import BaseLoader, RawDocument


class XlsxLoader(BaseLoader):
    """Loader genérico de Excel/CSV para búsqueda semántica.

    Convierte cada fila en una oración descriptiva ("columna: valor | columna: valor")
    para que sea embebible como texto. El archivo de inventario (`inventario_*.xlsx`)
    además se carga en una tabla estructurada aparte (ver app/db/inventory.py) para
    permitir consultas exactas (stock, caducidad, etc.) sin depender de similitud
    semántica.
    """

    def load(self, path: Path) -> list[RawDocument]:
        sheets = pd.read_excel(path, sheet_name=None, dtype=str)
        documents: list[RawDocument] = []

        for sheet_name, df in sheets.items():
            df = df.fillna("")
            for row_index, row in df.iterrows():
                pairs = [f"{col}: {value}" for col, value in row.items() if str(value).strip()]
                if not pairs:
                    continue
                content = " | ".join(pairs)
                documents.append(
                    RawDocument(
                        content=content,
                        metadata={
                            "source": path.name,
                            "sheet": sheet_name,
                            "row": int(row_index) + 2,  # +2: encabezado + índice base 1
                            "type": "xlsx",
                        },
                    )
                )
        return documents
