from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App metadata
    APP_NAME: str = "financial-agent"
    APP_VERSION: str = "2.2.0"
    ENVIRONMENT: str = "development"  # development, staging, production

    # Logging (K8s ready)
    LOG_LEVEL: str = "INFO"
    LOG_JSON_FORMAT: bool = True  # True for K8s, False for local dev

    # Authentication (from .env — no defaults for secrets)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Sysadmin credentials (from .env only)
    SYSADMIN_USERNAME: str
    SYSADMIN_EMAIL: str
    SYSADMIN_PASSWORD: str

    # Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    PASSWORD_MIN_LENGTH: int = 8
    STORAGE_SECRET: str

    # Database
    DATABASE_URL: str
    CHECKPOINT_PG_DSN: str = ""
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Ollama LLM
    OLLAMA_BASE_URL: str
    LLM_MODEL_NAME: str = "gpt-oss:20b"
    LLM_TEMPERATURE: float = 0.1
    LLM_KEEP_ALIVE: str = "4h"
    LLM_SEED: int = 42
    LLM_NUM_CTX: int = 16384  # Context window per la memoria conversazione
    LLM_TIMEOUT: int = 120  # Timeout in seconds

    # Qdrant Vector Store
    QDRANT_HOST: str
    QDRANT_PORT: int = 6333
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"
    QDRANT_TIMEOUT: int = 30

    # API Keys
    SERPAPI_API_KEY: str

    # Kubernetes / Health checks
    HEALTH_CHECK_TIMEOUT: int = 5

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
