from typing import Sequence

from app.core.config import Settings

from .base import EmbeddingsProvider

# Dimensión de salida del modelo cohere.embed-multilingual-v3.0 en OCI Generative AI.
_COHERE_MULTILINGUAL_V3_DIMENSIONS = 1024


class OCIGenAIEmbeddings(EmbeddingsProvider):
    """Embeddings de producción usando OCI Generative AI Service.

    Requiere: `oci` configurado (`~/.oci/config` o variables de entorno),
    permisos IAM sobre el compartment indicado y acceso habilitado al servicio
    Generative AI en la región elegida.
    """

    def __init__(self, settings: Settings):
        import oci  # import perezoso: evita requerir el SDK si no se usa este provider

        self._settings = settings
        config = oci.config.from_file(
            file_location=settings.oci_config_file, profile_name=settings.oci_config_profile
        )
        self._client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=config, service_endpoint=settings.oci_genai_endpoint
        )
        self._oci = oci

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        details = self._oci.generative_ai_inference.models.EmbedTextDetails(
            inputs=list(texts),
            serving_mode=self._oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=self._settings.oci_embed_model_id
            ),
            compartment_id=self._settings.oci_compartment_id,
            truncate="END",
            input_type="SEARCH_DOCUMENT",
        )
        response = self._client.embed_text(details)
        return list(response.data.embeddings)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]

    @property
    def dimensions(self) -> int:
        return _COHERE_MULTILINGUAL_V3_DIMENSIONS
