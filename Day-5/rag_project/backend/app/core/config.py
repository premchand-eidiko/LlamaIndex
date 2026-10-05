"""
Core Configuration Module

This module centralizes all configuration for the Enterprise RAG Assistant.
It uses Pydantic Settings to load configuration from environment variables
and .env files, providing type safety and validation.

Why we need this:
- Avoid hard-coding API keys, model names, and configuration values
- Provide a single source of truth for all settings
- Enable easy configuration changes without code modifications
- Support different environments (dev, staging, production)

What it does:
- Loads configuration from environment variables and .env files
- Validates configuration values using Pydantic
- Provides type-safe access to configuration throughout the application
"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Main settings class for the Enterprise RAG Assistant.

    Why BaseSettings?
    - Automatically reads from environment variables
    - Can load from .env files
    - Provides type validation
    - Supports default values
    """

    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # OpenAI API Configuration
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for LLM and embeddings"
    )

    # Groq API Configuration
    groq_api_key: str = Field(
        default="",
        description="Groq API key for high-speed LLM inference"
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model (e.g. llama-3.3-70b-versatile, llama3-70b-8192, mixtral-8x7b-32768)"
    )
    llm_provider: str = Field(
        default="auto",
        description="LLM provider: auto (prefers groq if set, then openai), groq, or openai"
    )

    # LLM Configuration
    llm_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="LLM model to use for query processing"
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation (0.0 = deterministic, 2.0 = creative)"
    )
    llm_max_tokens: int = Field(
        default=2000,
        gt=0,
        description="Maximum tokens in LLM response"
    )

    # Embedding Configuration
    embedding_provider: str = Field(
        default="auto",
        description="Embedding provider: auto (uses huggingface if no openai key), huggingface, or openai"
    )
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="Embedding model for vectorization (e.g. BAAI/bge-small-en-v1.5 or text-embedding-3-small)"
    )
    embedding_dimension: int = Field(
        default=384,
        gt=0,
        description="Dimension of embedding vectors (384 for bge-small, 1536 for OpenAI)"
    )

    # Storage Configuration
    storage_dir: str = Field(
        default=str(_BACKEND_DIR / "data" / "storage"),
        description="Directory for persistent storage (indexes, docstore, etc.)"
    )
    documents_dir: str = Field(
        default=str(_BACKEND_DIR / "data" / "documents"),
        description="Directory for uploaded documents"
    )

    # Retrieval Configuration
    similarity_top_k: int = Field(
        default=10,
        gt=0,
        description="Number of similar nodes to retrieve initially"
    )
    rerank_top_k: int = Field(
        default=5,
        gt=0,
        description="Number of nodes to use after re-ranking"
    )

    # Graph Configuration
    graph_store_type: str = Field(
        default="memory",
        description="Type of graph store: memory, neo4j, or falkordb"
    )
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: str = Field(
        default="",
        description="Neo4j password"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="Host for FastAPI server"
    )
    api_port: int = Field(
        default=8000,
        gt=0,
        le=65535,
        description="Port for FastAPI server"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR"
    )


# Global settings instance
# This is imported throughout the application to access configuration
settings = Settings()
