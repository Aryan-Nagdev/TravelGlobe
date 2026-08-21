import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "TravelGuard AI"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "*"

    # Groq
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")

    # Supabase
    SUPABASE_URL: str = Field(default="", env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(default="", env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="", env="SUPABASE_SERVICE_ROLE_KEY")

    # OpenWeather
    OPENWEATHER_API_KEY: str = Field(default="", env="OPENWEATHER_API_KEY")
    OPENWEATHER_UNITS: str = "metric"

    # Geospatial APIs
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = "TravelGuardAI/1.0 (travel@example.com)"
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    PHOTON_API_URL: str = "https://photon.komoot.io/api/"
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"

    # Copernicus
    COPERNICUS_DATA_SPACE_URL: str = "https://dataspace.copernicus.eu/"
    COPERNICUS_USERNAME: str = ""
    COPERNICUS_PASSWORD: str = ""

    # RAG Vector Store
    CHROMA_PERSIST_DIR: str = "data/chroma"
    RAG_TOP_K: int = 8
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
