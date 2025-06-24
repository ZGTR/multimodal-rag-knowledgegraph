from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path
from src.bootstrap.logger import get_logger

logger = get_logger("settings")

class Settings(BaseSettings):
    app_env: Literal["dev", "prod"] = "dev"
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    aws_region: str = "eu-west-2"
    vectordb_uri: str | None = None
    embedding_model_name: str = "text-embedding-3-small"
    kg_backend: Literal["neptune", "neo4j", "dgraph"] = "neptune"
    kg_uri: str | None = None
    transcripts_bucket: str = "kg-rag-transcripts"
    openai_api_key: str | None = None
    bedrock_region: str | None = None
    bedrock_model_id: str | None = None
    
    # Twitter API settings
    twitter_bearer_token: str | None = None
    
    # Instagram API settings
    instagram_access_token: str | None = None
    
    model_config = SettingsConfigDict(env_file="local.env", case_sensitive=False)

settings = Settings()
logger.info(f"Settings loaded: app_env={settings.app_env}, vectordb_uri={settings.vectordb_uri}, kg_uri={settings.kg_uri}")
