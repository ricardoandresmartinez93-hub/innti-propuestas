"""
Configuración centralizada del proyecto.
Todas las variables de entorno se cargan aquí.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    # Base de datos
    database_url: str = "sqlite:///./innti_propuestas.db"

    # Innti (IA Corporativa)
    innti_api_base: str = "https://litellm.quipux.com/v1"
    innti_api_key: str = ""
    innti_model: str = "gpt-4o-mini"

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Portafolio
    portfolio_file_path: str = "../../../ListaPortafolio.xlsx"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Singleton de configuración (cacheado)."""
    return Settings()
