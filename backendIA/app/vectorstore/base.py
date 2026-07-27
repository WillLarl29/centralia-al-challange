from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float


class VectorStoreProvider(ABC):
    """Interfaz común para almacenar y buscar embeddings (local o Oracle 23ai)."""

    @abstractmethod
    def upsert(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def similarity_search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError
