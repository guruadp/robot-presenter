from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Required — missing keys raise a ValidationError with the field name listed
    OPENAI_API_KEY: str

    # Optional with sensible defaults
    ELEVENLABS_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./data/ednex.db"
    STORAGE_DIR: str = "./data/storage"
    CHROMA_DIR: str = "./data/chroma"
    LOG_LEVEL: str = "INFO"
    TTS_PROVIDER: str = "openai"  # openai | free-local
    OPENAI_TTS_MODEL: str = "gpt-4o-mini-tts"
    OPENAI_TTS_VOICE: str = "marin"


@lru_cache
def get_settings() -> Settings:
    return Settings()
