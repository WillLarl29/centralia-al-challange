from app.core.config import Settings

from .base import ChatMessage, GroundedDocument, LLMAnswer, LLMProvider


class OCIGenAIChat(LLMProvider):
    """Chat de producción usando OCI Generative AI Service (modelo Cohere Command R+).

    Se apoya en el soporte nativo de "documents" + "citations" de la API de chat
    de Cohere en OCI: se le pasan los fragmentos recuperados como `documents` y el
    propio modelo genera la respuesta grounded, devolviendo las citas exactas que
    usó (evita alucinaciones y facilita mostrar la fuente en el frontend).

    Requiere: `oci` configurado y acceso habilitado al servicio Generative AI.
    """

    def __init__(self, settings: Settings):
        import oci  # import perezoso: evita requerir el SDK si no se usa este provider

        self._settings = settings
        self._oci = oci
        config = oci.config.from_file(
            file_location=settings.oci_config_file, profile_name=settings.oci_config_profile
        )
        self._client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=config, service_endpoint=settings.oci_genai_endpoint
        )

    def generate(
        self,
        system_prompt: str,
        history: list[ChatMessage],
        question: str,
        documents: list[GroundedDocument],
    ) -> LLMAnswer:
        models = self._oci.generative_ai_inference.models

        chat_history = [
            models.CohereUserMessage(message=m.content) if m.role == "user" else models.CohereChatBotMessage(message=m.content)
            for m in history
        ]

        chat_request = models.CohereChatRequest(
            message=question,
            preamble_override=system_prompt,
            chat_history=chat_history,
            documents=[{"id": doc.id, "source": doc.source, "text": doc.text} for doc in documents],
            is_stream=False,
            max_tokens=800,
            temperature=0.2,
        )

        details = models.ChatDetails(
            compartment_id=self._settings.oci_compartment_id,
            serving_mode=models.OnDemandServingMode(model_id=self._settings.oci_chat_model_id),
            chat_request=chat_request,
        )

        response = self._client.chat(details)
        chat_response = response.data.chat_response

        cited_sources = sorted(
            {
                citation_doc_id
                for citation in getattr(chat_response, "citations", []) or []
                for citation_doc_id in getattr(citation, "document_ids", [])
            }
        )

        return LLMAnswer(text=chat_response.text, used_fallback=False, cited_sources=list(cited_sources))
