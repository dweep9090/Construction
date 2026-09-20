from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str = "change-me-default-secret-for-dev"
    JWT_EXPIRE_MINUTES: int = 480
    CORS_ORIGINS: List[str] | str = ["http://localhost:5173"]
    
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    AI_PROVIDER: str = "huggingface"
    HF_TOKEN: str | None = None
    AI_MODEL: str = "openai/gpt-oss-120b:fastest"

    class Config:
        env_file = ".env"

settings = Settings()
