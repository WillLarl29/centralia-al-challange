from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter()


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "embeddings_provider": settings.embeddings_provider,
        "vectorstore_provider": settings.vectorstore_provider,
        "llm_provider": settings.llm_provider,
    }
