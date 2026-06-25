"""App configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "LocalModel HQ"
    OLLAMA_URL: str = "http://localhost:11434"
    STATIC_DIR: str = ""
    TEMPLATES_DIR: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()

CATALOG_PATH = Path(__file__).parent / "static" / "catalog.json"
