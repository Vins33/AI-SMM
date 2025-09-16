from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    OLLAMA_BASE_URL: str
    QDRANT_HOST: str
    QDRANT_PORT: int = 6333
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"
    LLM_MODEL_NAME: str = "gpt-oss:20b"
    SERPAPI_API_KEY: str

settings = Settings()
