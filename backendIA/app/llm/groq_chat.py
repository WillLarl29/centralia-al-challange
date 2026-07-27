import httpx

from app.core.config import Settings

from .base import ChatMessage, GroundedDocument, LLMAnswer, LLMProvider

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqChat(LLMProvider):
    """Chat vía Groq (API compatible con OpenAI). Alternativa gratuita mientras
    no se tenga OCI Generative AI Service habilitado. Modelo por defecto:
    `llama-3.3-70b-versatile`.

    A diferencia de OCI Generative AI (Cohere), Groq no soporta el parámetro
    nativo `documents` con citas automáticas, así que los fragmentos
    recuperados se inyectan como contexto en el prompt de sistema y se le
    pide al modelo que cite la fuente explícitamente en el texto.
    """

    def __init__(self, settings: Settings):
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY no está configurado en .env (requerido para LLM_PROVIDER=groq)")

        self._settings = settings
        self._client = httpx.Client(
            base_url=_GROQ_BASE_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            timeout=60.0,
        )

    @staticmethod
    def _build_context(documents: list[GroundedDocument]) -> str:
        if not documents:
            return ""
        parts = [f"[Fuente: {doc.source}]\n{doc.text}" for doc in documents]
        return "\n\n---\n\n".join(parts)

    def generate(
        self,
        system_prompt: str,
        history: list[ChatMessage],
        question: str,
        documents: list[GroundedDocument],
    ) -> LLMAnswer:
        context = self._build_context(documents)
        system_content = (
            f"{system_prompt}\n\nDocumentos internos recuperados como contexto:\n\n{context}"
            if context
            else system_prompt
        )

        messages = [{"role": "system", "content": system_content}]
        messages.extend({"role": m.role, "content": m.content} for m in history)
        messages.append({"role": "user", "content": question})

        response = self._client.post(
            "/chat/completions",
            json={
                "model": self._settings.groq_model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1024,
            },
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]

        return LLMAnswer(
            text=text,
            used_fallback=False,
            cited_sources=[doc.source for doc in documents],
        )
