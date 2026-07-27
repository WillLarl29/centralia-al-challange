"""CLI para ingestar todos los documentos de `documents/` en el vector store
(y el inventario en la tabla estructurada). Uso:

    cd backendIA
    python -m scripts.ingest_documents
"""

from app.core.config import get_settings
from app.ingestion import run_ingestion


def main() -> None:
    settings = get_settings()
    print(f"Ingestando documentos desde: {settings.documents_path}")
    print(f"Providers -> embeddings={settings.embeddings_provider} vectorstore={settings.vectorstore_provider}")

    stats = run_ingestion(settings)

    print("\n--- Resumen de ingesta ---")
    print(f"Archivos escaneados : {stats.files_scanned}")
    print(f"Archivos omitidos   : {stats.files_skipped}")
    print(f"Chunks indexados    : {stats.chunks_indexed}")
    print(f"Filas de inventario : {stats.inventory_rows_loaded}")


if __name__ == "__main__":
    main()
