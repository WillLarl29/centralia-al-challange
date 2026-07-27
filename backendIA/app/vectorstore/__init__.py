from app.core.config import Settings

from .base import SearchResult, VectorStoreProvider
from .local_store import LocalNumpyVectorStore


def get_vectorstore_provider(settings: Settings) -> VectorStoreProvider:
    if settings.vectorstore_provider == "oracle23ai":
        from .oracle23ai import Oracle23aiVectorStore

        return Oracle23aiVectorStore(settings)
    return LocalNumpyVectorStore(settings.data_path / "vector_store")


__all__ = ["VectorStoreProvider", "SearchResult", "get_vectorstore_provider"]
