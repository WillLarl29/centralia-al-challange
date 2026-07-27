from dataclasses import dataclass

from app.core.config import Settings
from app.llm import ChatMessage, GroundedDocument, LLMProvider

from . import sql_tool
from .prompts import SYSTEM_PROMPT
from .retriever import Retriever


@dataclass
class AgentAnswer:
    text: str
    sources: list[dict]
    used_fallback: bool


class CentralIAAgent:
    """Orquesta: recuperación semántica (RAG) + consulta estructurada de
    inventario (tool) + generación con LLM grounded en ambas fuentes."""

    def __init__(self, settings: Settings, retriever: Retriever, llm: LLMProvider):
        self._settings = settings
        self._retriever = retriever
        self._llm = llm

    def answer(self, question: str, history: list[ChatMessage] | None = None) -> AgentAnswer:
        history = history or []

        search_results = self._retriever.retrieve(question)
        documents = [
            GroundedDocument(
                id=result.id,
                text=result.text,
                source=f"{result.metadata.get('source', 'desconocido')}"
                + (f" (pág. {result.metadata['page']})" if "page" in result.metadata else ""),
            )
            for result in search_results
        ]

        inventory_context = sql_tool.query_inventory_context(self._settings, question)
        if inventory_context:
            documents.append(
                GroundedDocument(
                    id="inventario-estructurado",
                    text=inventory_context,
                    source="inventario_de_supermercado_latam.xlsx (consulta estructurada)",
                )
            )

        llm_answer = self._llm.generate(
            system_prompt=SYSTEM_PROMPT,
            history=history,
            question=question,
            documents=documents,
        )

        sources = [
            {"id": result.id, "source": doc.source, "score": result.score, "text": result.text[:300]}
            for result, doc in zip(search_results, documents)
        ]
        if inventory_context:
            sources.append({"id": "inventario-estructurado", "source": documents[-1].source, "score": None, "text": inventory_context[:300]})

        return AgentAnswer(text=llm_answer.text, sources=sources, used_fallback=llm_answer.used_fallback)
