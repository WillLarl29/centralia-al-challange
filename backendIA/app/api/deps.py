from functools import lru_cache

from app.core.config import Settings, get_settings
from app.embeddings import get_embeddings_provider
from app.llm import get_llm_provider
from app.rag import CentralIAAgent, Retriever
from app.vectorstore import get_vectorstore_provider


@lru_cache
def get_agent() -> CentralIAAgent:
    settings: Settings = get_settings()
    embeddings = get_embeddings_provider(settings)
    vectorstore = get_vectorstore_provider(settings)
    llm = get_llm_provider(settings)
    retriever = Retriever(settings, embeddings, vectorstore)
    return CentralIAAgent(settings, retriever, llm)
