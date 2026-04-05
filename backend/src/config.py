from pydantic import field_validator
from pydantic_settings import BaseSettings

_DEFAULT_SECRET = "change-me-to-a-long-random-string"


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nexus:nexus@localhost:5432/nexusai"

    # Security
    SECRET_KEY: str = _DEFAULT_SECRET
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15       # reduced from 60 — short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7           # long-lived refresh tokens

    # Ollama (remote shared server)
    OLLAMA_BASE_URL: str = "http://10.1.76.234:11434"
    OLLAMA_MODEL: str = "gpt-oss"

    # Anthropic Claude (fallback LLM)
    ANTHROPIC_API_KEY: str = ""

    # LinkedIn (job market data)
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""

    # MCP server URLs
    MCP_STUDENT_DB_URL: str = "http://localhost:9001"
    MCP_JOB_MARKET_URL: str = "http://localhost:9002"
    MCP_RESOURCE_RAG_URL: str = "http://localhost:9003"
    MCP_COUNSELOR_ALERTS_URL: str = "http://localhost:9004"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_secure(cls, v: str) -> str:
        if v == _DEFAULT_SECRET:
            raise ValueError(
                "\n\nSECRET_KEY is still set to the insecure default value!\n"
                "Generate a secure key and add it to your .env file:\n"
                "  python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            )
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    class Config:
        env_file = ".env"


settings = Settings()
