import os
from pathlib import Path

from dotenv import load_dotenv


# ==================================================
# Base Directories
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DOCUMENTS_DIR = DATA_DIR / "documents"

STORAGE_DIR = DATA_DIR / "storage"


# ==================================================
# Environment
# ==================================================

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ==================================================
# Groq
# ==================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-120b",
)


# ==================================================
# Embedding Model
# ==================================================

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-en-v1.5",
)


# ==================================================
# RAG Configuration
# ==================================================

CHUNK_SIZE = int(
    os.getenv(
        "CHUNK_SIZE",
        "512",
    )
)


CHUNK_OVERLAP = int(
    os.getenv(
        "CHUNK_OVERLAP",
        "50",
    )
)


SIMILARITY_TOP_K = int(
    os.getenv(
        "SIMILARITY_TOP_K",
        "5",
    )
)


# ==================================================
# Create Required Directories
# ==================================================

DOCUMENTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ==================================================
# Validate Groq API Key
# ==================================================

if not GROQ_API_KEY:

    raise ValueError(
        "GROQ_API_KEY is missing. "
        "Add it to backend/.env"
    )