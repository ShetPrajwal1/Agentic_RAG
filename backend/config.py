import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    openai_api_key: SecretStr
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    langsmith_api_key: SecretStr | None = None
    langchain_tracing_v2: str = "false"
    langchain_project: str = "automotive_graphrag"
    
    # Chroma DB settings
    chroma_persist_directory: str = "./chroma_db"
    
    # Text Splitter settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
