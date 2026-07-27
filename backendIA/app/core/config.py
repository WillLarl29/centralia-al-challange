from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CentralIA"
    environment: str = "local"

    documents_dir: str = "../documents"
    data_dir: str = "./data"
    allowed_origins: str = "http://localhost:5173"

    chunk_size: int = 900
    chunk_overlap: int = 150
    top_k: int = 5

    embeddings_provider: str = "local"  # local | oci
    llm_provider: str = "local"  # local | oci
    vectorstore_provider: str = "local"  # local | oracle23ai

    # OCI Generative AI
    oci_config_file: str = "~/.oci/config"
    oci_config_profile: str = "DEFAULT"
    oci_genai_endpoint: str = ""
    oci_compartment_id: str = ""
    oci_embed_model_id: str = "cohere.embed-multilingual-v3.0"
    oci_chat_model_id: str = "cohere.command-r-plus"

    # Oracle Autonomous Database 23ai
    oracle_db_user: str = ""
    oracle_db_password: str = ""
    oracle_db_dsn: str = ""
    oracle_db_wallet_location: str = ""
    oracle_db_wallet_password: str = ""

    @property
    def documents_path(self) -> Path:
        path = Path(self.documents_dir)
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()

    @property
    def data_path(self) -> Path:
        path = Path(self.data_dir)
        resolved = path if path.is_absolute() else (BACKEND_DIR / path).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
