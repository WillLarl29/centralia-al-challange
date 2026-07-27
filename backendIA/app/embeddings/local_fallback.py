from typing import Sequence

from sklearn.feature_extraction.text import HashingVectorizer

from .base import EmbeddingsProvider


class LocalHashingEmbeddings(EmbeddingsProvider):
    """Embeddings 100% locales basados en feature hashing (sin descargas ni API keys).

    No tienen la calidad semántica de un modelo entrenado (p. ej. Cohere en OCI
    Generative AI), pero permiten correr y probar todo el pipeline de ingesta y
    recuperación (RAG) de punta a punta sin depender de la nube. Pensado como
    `EMBEDDINGS_PROVIDER=local` para desarrollo; en producción usar `oci`.
    """

    def __init__(self, n_features: int = 1024):
        self._n_features = n_features
        self._vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm="l2",
            ngram_range=(1, 2),
            lowercase=True,
        )

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        matrix = self._vectorizer.transform(list(texts))
        return matrix.toarray().tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    @property
    def dimensions(self) -> int:
        return self._n_features
