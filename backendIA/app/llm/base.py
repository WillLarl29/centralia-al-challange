from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class GroundedDocument:
    """Un fragmento recuperado que se pasa al LLM como evidencia (grounding)."""

    id: str
    text: str
    source: str


@dataclass
class LLMAnswer:
    text: str
    used_fallback: bool = False
    cited_sources: list[str] = field(default_factory=list)


class LLMProvider(ABC):
    """Interfaz común para generar respuestas conversacionales grounded en documentos."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        history: list[ChatMessage],
        question: str,
        documents: list[GroundedDocument],
    ) -> LLMAnswer:
        raise NotImplementedError
