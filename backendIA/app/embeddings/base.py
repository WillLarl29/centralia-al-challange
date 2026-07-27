from abc import ABC, abstractmethod
from typing import Sequence


class EmbeddingsProvider(ABC):
    """Interfaz común para generar embeddings, sea con OCI Generative AI o localmente."""

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        raise NotImplementedError
