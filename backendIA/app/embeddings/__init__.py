from app.core.config import Settings

from .base import EmbeddingsProvider
from .local_fallback import LocalHashingEmbeddings


def get_embeddings_provider(settings: Settings) -> EmbeddingsProvider:
    if settings.embeddings_provider == "oci":
        from .oci_genai_embeddings import OCIGenAIEmbeddings

        return OCIGenAIEmbeddings(settings)
    return LocalHashingEmbeddings()


__all__ = ["EmbeddingsProvider", "get_embeddings_provider"]
