import sqlite3
from pathlib import Path

import pandas as pd

from app.core.config import Settings

_TABLE_NAME = "inventario"

# Nombres de columnas esperados en el Excel de inventario (ver documents/inventario_de_supermercado_latam.xlsx).
_EXPECTED_COLUMNS = [
    "SKU",
    "Código de Barras (EAN)",
    "Descripción",
    "Marca",
    "Categoría",
    "Subcategoría",
    "UN",
    "Ubicación",
    "Stock Actual",
    "Stock Mínimo",
    "Stock Máximo",
    "Lote",
    "Fecha de Fabricación",
    "Fecha de Vencimiento",
    "Costo Unitario",
    "Precio de Venta Unitario",
    "Proveedor Principal",
    "Tiempo de Reposición",
]


def _db_path(settings: Settings) -> Path:
    return settings.data_path / "inventory.db"


def load_inventory_file(settings: Settings, xlsx_path: Path) -> int:
    """Carga el Excel de inventario a una tabla SQLite local para consultas exactas
    (stock, caducidad, proveedor, etc.), separado del texto embebido para RAG."""
    df = pd.read_excel(xlsx_path, dtype=str).fillna("")
    df.columns = [str(c).strip() for c in df.columns]

    for numeric_col in ["Stock Actual", "Stock Mínimo", "Stock Máximo", "Costo Unitario", "Precio de Venta Unitario"]:
        if numeric_col in df.columns:
            df[numeric_col] = pd.to_numeric(df[numeric_col], errors="coerce")

    connection = sqlite3.connect(_db_path(settings))
    try:
        df.to_sql(_TABLE_NAME, connection, if_exists="replace", index=False)
        connection.commit()
    finally:
        connection.close()

    return len(df)


def _connect(settings: Settings) -> sqlite3.Connection:
    connection = sqlite3.connect(_db_path(settings))
    connection.row_factory = sqlite3.Row
    return connection


def _table_exists(connection: sqlite3.Connection) -> bool:
    cursor = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (_TABLE_NAME,)
    )
    return cursor.fetchone() is not None


def search_by_name(settings: Settings, keyword: str, limit: int = 10) -> list[dict]:
    """Busca productos cuya descripción contenga `keyword` (case-insensitive)."""
    connection = _connect(settings)
    try:
        if not _table_exists(connection):
            return []
        rows = connection.execute(
            f'SELECT * FROM {_TABLE_NAME} WHERE "Descripción" LIKE ? LIMIT ?',
            (f"%{keyword}%", limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def expiring_within_days(settings: Settings, days: int, limit: int = 20) -> list[dict]:
    """Productos cuya Fecha de Vencimiento cae dentro de los próximos `days` días."""
    connection = _connect(settings)
    try:
        if not _table_exists(connection):
            return []
        rows = connection.execute(
            f"""
            SELECT * FROM {_TABLE_NAME}
            WHERE date("Fecha de Vencimiento") <= date('now', ? || ' days')
            ORDER BY date("Fecha de Vencimiento") ASC
            LIMIT ?
            """,
            (str(days), limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def low_stock(settings: Settings, limit: int = 20) -> list[dict]:
    """Productos cuyo Stock Actual está en o por debajo del Stock Mínimo."""
    connection = _connect(settings)
    try:
        if not _table_exists(connection):
            return []
        rows = connection.execute(
            f'SELECT * FROM {_TABLE_NAME} WHERE "Stock Actual" <= "Stock Mínimo" LIMIT ?',
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def by_supplier(settings: Settings, supplier_keyword: str, limit: int = 20) -> list[dict]:
    connection = _connect(settings)
    try:
        if not _table_exists(connection):
            return []
        rows = connection.execute(
            f'SELECT * FROM {_TABLE_NAME} WHERE "Proveedor Principal" LIKE ? LIMIT ?',
            (f"%{supplier_keyword}%", limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
