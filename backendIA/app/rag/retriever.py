from app.core.config import Settings
from app.embeddings import EmbeddingsProvider
from app.vectorstore import SearchResult, VectorStoreProvider


class Retriever:
    def __init__(self, settings: Settings, embeddings: EmbeddingsProvider, vectorstore: VectorStoreProvider):
        self._settings = settings
        self._embeddings = embeddings
        self._vectorstore = vectorstore

    def retrieve(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        query_embedding = self._embeddings.embed_query(query)
        return self._vectorstore.similarity_search(query_embedding, top_k or self._settings.top_k)
