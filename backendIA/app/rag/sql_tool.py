import re

from app.core.config import Settings
from app.db import inventory

_STOCK_KEYWORDS = ("stock", "existencia", "inventario", "cuántas unidades", "cuánto queda")
_EXPIRY_KEYWORDS = ("vence", "vencimiento", "caduc", "expira")
_SUPPLIER_KEYWORDS = ("proveedor", "supplier")
_DAYS_PATTERN = re.compile(r"(\d+)\s*d[ií]as")


def looks_like_inventory_question(question: str) -> bool:
    lowered = question.lower()
    return any(kw in lowered for kw in _STOCK_KEYWORDS + _EXPIRY_KEYWORDS + _SUPPLIER_KEYWORDS)


def _format_rows(rows: list[dict]) -> str:
    if not rows:
        return "(sin resultados en la tabla de inventario)"

    lines = []
    for row in rows[:10]:
        lines.append(
            f"SKU {row.get('SKU', '?')} — {row.get('Descripción', '?')} | "
            f"Stock actual: {row.get('Stock Actual', '?')} | "
            f"Stock mínimo: {row.get('Stock Mínimo', '?')} | "
            f"Vencimiento: {row.get('Fecha de Vencimiento', '?')} | "
            f"Proveedor: {row.get('Proveedor Principal', '?')}"
        )
    return "\n".join(lines)


def query_inventory_context(settings: Settings, question: str) -> str | None:
    """Router basado en palabras clave: ejecuta la consulta estructurada más
    relevante sobre el inventario y devuelve un resumen textual para inyectar
    como contexto adicional al LLM. Usa solo funciones parametrizadas (nunca SQL
    libre generado por el modelo) para evitar inyección SQL."""
    lowered = question.lower()

    if any(kw in lowered for kw in _EXPIRY_KEYWORDS):
        days_match = _DAYS_PATTERN.search(lowered)
        days = int(days_match.group(1)) if days_match else 7
        rows = inventory.expiring_within_days(settings, days=days)
        return f"Productos que vencen en los próximos {days} días:\n{_format_rows(rows)}"

    if "bajo" in lowered and "stock" in lowered or "reponer" in lowered or "agotando" in lowered:
        rows = inventory.low_stock(settings)
        return f"Productos con stock en o por debajo del mínimo:\n{_format_rows(rows)}"

    if any(kw in lowered for kw in _SUPPLIER_KEYWORDS):
        # Extrae una palabra clave simple del proveedor (heurística; se puede
        # mejorar con NER o function-calling real del LLM).
        words = [w for w in re.findall(r"[A-ZÁÉÍÓÚa-záéíóú]+", question) if len(w) > 3]
        keyword = words[-1] if words else ""
        rows = inventory.by_supplier(settings, keyword) if keyword else []
        return f"Productos del proveedor '{keyword}':\n{_format_rows(rows)}"

    if any(kw in lowered for kw in _STOCK_KEYWORDS):
        words = [w for w in re.findall(r"[A-ZÁÉÍÓÚa-záéíóú]+", question) if len(w) > 3]
        keyword = words[-1] if words else ""
        rows = inventory.search_by_name(settings, keyword) if keyword else []
        return f"Resultados de inventario para '{keyword}':\n{_format_rows(rows)}"

    return None
