import shutil
import tempfile
import uuid
from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings

from llama_index.embeddings.huggingface import (
    HuggingFaceEmbedding,
)
from llama_index.llms.groq import Groq

from app.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_DIR,
    DOCUMENTS_DIR,
    EMBEDDING_MODEL,
    GROQ_API_KEY,
    LLM_MODEL,
    STORAGE_DIR,
)


# ==================================================
# LLM
# ==================================================

Settings.llm = Groq(
    model=LLM_MODEL,
    api_key=GROQ_API_KEY,
)


# ==================================================
# Embedding Model
# ==================================================

Settings.embed_model = HuggingFaceEmbedding(
    model_name=EMBEDDING_MODEL,
)


# ==================================================
# Node Parser
# ==================================================

splitter = SentenceSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)


def clear_index_storage() -> None:
    """Remove persisted node, vector, and index files."""
    shutil.rmtree(STORAGE_DIR, ignore_errors=True)


# ==================================================
# Ingestion
# ==================================================

def ingest_documents() -> VectorStoreIndex | None:
    """
    Complete ingestion pipeline:

    Documents
        ↓
    Nodes
        ↓
    Embeddings
        ↓
    VectorStoreIndex
        ↓
    Persistent Storage
    """

    supported_extensions = {
        ".pdf",
        ".txt",
        ".md",
        ".csv",
        ".docx",
    }
    has_documents = any(
        path.is_file() and path.suffix.lower() in supported_extensions
        for path in DOCUMENTS_DIR.rglob("*")
    )

    if not has_documents:
        clear_index_storage()
        return None

    documents = SimpleDirectoryReader(
        input_dir=str(DOCUMENTS_DIR),
        recursive=True,
    ).load_data()


    if not documents:
        clear_index_storage()
        return None


    print(
        f"Loaded {len(documents)} document(s)."
    )


    # --------------------------------------------------
    # Documents → Nodes
    # --------------------------------------------------

    nodes = splitter.get_nodes_from_documents(
        documents
    )


    print(
        f"Created {len(nodes)} nodes."
    )


    # --------------------------------------------------
    # Nodes → VectorStoreIndex
    # --------------------------------------------------

    index = VectorStoreIndex(nodes)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=".storage-rebuild-",
            dir=DATA_DIR,
        )
    )
    backup_dir = DATA_DIR / f".storage-backup-{uuid.uuid4().hex}"

    try:
        index.storage_context.persist(
            persist_dir=str(staging_dir)
        )

        if STORAGE_DIR.exists():
            STORAGE_DIR.rename(backup_dir)

        try:
            staging_dir.rename(STORAGE_DIR)
        except Exception:
            if backup_dir.exists() and not STORAGE_DIR.exists():
                backup_dir.rename(STORAGE_DIR)
            raise

        shutil.rmtree(backup_dir, ignore_errors=True)
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


    print(
        f"Index persisted to: {STORAGE_DIR}"
    )


    return index