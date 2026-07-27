from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.db import inventory
from app.embeddings import get_embeddings_provider
from app.vectorstore import get_vectorstore_provider

from .chunker import build_chunks
from .loaders import SUPPORTED_EXTENSIONS, get_loader_for

# Heurística simple: si el nombre del archivo sugiere que es el inventario,
# además de indexarlo para búsqueda semántica se carga en la tabla estructurada
# (app/db/inventory.py) para permitir consultas exactas de stock/caducidad.
_INVENTORY_HINTS = ("inventario", "inventory", "stock")


@dataclass
class IngestionStats:
    files_scanned: int = 0
    files_skipped: int = 0
    chunks_indexed: int = 0
    inventory_rows_loaded: int = 0


def _looks_like_inventory(path: Path) -> bool:
    name = path.stem.lower()
    return any(hint in name for hint in _INVENTORY_HINTS) and path.suffix.lower() in {".xlsx", ".xls"}


def run_ingestion(settings: Settings) -> IngestionStats:
    stats = IngestionStats()
    embeddings_provider = get_embeddings_provider(settings)
    vectorstore_provider = get_vectorstore_provider(settings)

    documents_dir = settings.documents_path
    if not documents_dir.exists():
        raise FileNotFoundError(f"No existe el directorio de documentos: {documents_dir}")

    for path in sorted(documents_dir.rglob("*")):
        if not path.is_file():
            continue

        stats.files_scanned += 1

        if _looks_like_inventory(path):
            rows = inventory.load_inventory_file(settings, path)
            stats.inventory_rows_loaded += rows
            print(f"[inventario] {path.name}: {rows} filas cargadas en tabla estructurada")

        loader = get_loader_for(path)
        if loader is None:
            stats.files_skipped += 1
            print(f"[omitido] {path.name}: extensión no soportada ({sorted(SUPPORTED_EXTENSIONS)})")
            continue

        raw_documents = loader.load(path)
        all_texts: list[str] = []
        all_ids: list[str] = []
        all_metadatas: list[dict] = []

        for raw_document in raw_documents:
            for chunk in build_chunks(raw_document, settings.chunk_size, settings.chunk_overlap):
                all_ids.append(chunk.id)
                all_texts.append(chunk.text)
                all_metadatas.append(chunk.metadata)

        if not all_texts:
            print(f"[vacío] {path.name}: no se extrajo texto")
            continue

        embeddings = embeddings_provider.embed_documents(all_texts)
        vectorstore_provider.upsert(ids=all_ids, texts=all_texts, embeddings=embeddings, metadatas=all_metadatas)
        stats.chunks_indexed += len(all_texts)
        print(f"[indexado] {path.name}: {len(all_texts)} chunks")

    return stats
