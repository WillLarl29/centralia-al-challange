from .base import ChatMessage, GroundedDocument, LLMAnswer, LLMProvider


class ExtractiveFallbackLLM(LLMProvider):
    """Fallback sin modelo generativo: devuelve los fragmentos más relevantes ya
    recuperados, con su fuente, en vez de una respuesta redactada por un LLM.

    Sirve para probar el pipeline de ingesta + recuperación de punta a punta sin
    necesidad de credenciales de OCI Generative AI. En producción, usar
    `LLM_PROVIDER=oci` (ver `oci_genai.py`).
    """

    def generate(
        self,
        system_prompt: str,
        history: list[ChatMessage],
        question: str,
        documents: list[GroundedDocument],
    ) -> LLMAnswer:
        if not documents:
            return LLMAnswer(
                text=(
                    "No encontré información relacionada en los documentos internos de "
                    "Mercado Central 24h. (Modo local sin LLM: configura OCI Generative AI "
                    "para respuestas conversacionales completas.)"
                ),
                used_fallback=True,
            )

        lines = [
            "Modo local sin LLM generativo — fragmentos más relevantes encontrados "
            "(configura LLM_PROVIDER=oci para una respuesta redactada y con razonamiento):",
            "",
        ]
        for doc in documents:
            snippet = doc.text.strip().replace("\n", " ")
            snippet = snippet[:400] + ("…" if len(snippet) > 400 else "")
            lines.append(f"• [{doc.source}] {snippet}")

        return LLMAnswer(
            text="\n".join(lines),
            used_fallback=True,
            cited_sources=[doc.source for doc in documents],
        )
