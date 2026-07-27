from app.core.config import Settings

from .base import ChatMessage, GroundedDocument, LLMAnswer, LLMProvider
from .local_fallback import ExtractiveFallbackLLM


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "oci":
        from .oci_genai import OCIGenAIChat

        return OCIGenAIChat(settings)
    return ExtractiveFallbackLLM()


__all__ = ["LLMProvider", "ChatMessage", "GroundedDocument", "LLMAnswer", "get_llm_provider"]
