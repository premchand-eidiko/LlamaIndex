import os
from pathlib import Path

from dotenv import load_dotenv


# ==================================================
# PROJECT DIRECTORY STRUCTURE
# ==================================================
#
# backend/
#     app/
#     data/
#         documents/
#         storage/
#         chat_history.db
#
# BASE_DIR points to:
#
# /home/bandaru/prem/LlamaIndex/Day-5/project/backend
#
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==================================================
# DATA DIRECTORIES
# ==================================================

DATA_DIR = BASE_DIR / "data"

DOCUMENTS_DIR = DATA_DIR / "documents"

STORAGE_DIR = DATA_DIR / "storage"

CHAT_DATABASE = DATA_DIR / "chat_history.db"


# ==================================================
# ENVIRONMENT VARIABLES
# ==================================================

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ==================================================
# GROQ CONFIGURATION
# ==================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-120b",
)


# ==================================================
# EMBEDDING MODEL
# ==================================================

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-en-v1.5",
)


# ==================================================
# RERANKER MODEL
# ==================================================

RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "BAAI/bge-reranker-base",
)


# ==================================================
# CHUNKING
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


# ==================================================
# RETRIEVAL
# ==================================================

SIMILARITY_TOP_K = int(
    os.getenv(
        "SIMILARITY_TOP_K",
        "5",
    )
)

HYBRID_TOP_K = int(
    os.getenv(
        "HYBRID_TOP_K",
        "10",
    )
)

RERANK_TOP_N = int(
    os.getenv(
        "RERANK_TOP_N",
        "5",
    )
)


# ==================================================
# CREATE REQUIRED DIRECTORIES
# ==================================================

DOCUMENTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ==================================================
# VALIDATE REQUIRED SETTINGS
# ==================================================

if not GROQ_API_KEY:

    raise ValueError(
        "GROQ_API_KEY is missing. "
        "Add it to backend/.env"
    )