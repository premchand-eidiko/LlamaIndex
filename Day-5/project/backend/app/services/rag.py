from llama_index.core import (
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.settings import Settings

from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from app.config import (
    STORAGE_DIR,
    GROQ_API_KEY,
    LLM_MODEL,
    EMBEDDING_MODEL,
    SIMILARITY_TOP_K,
)


# --------------------------------------------------
# LLM
# --------------------------------------------------

Settings.llm = Groq(
    model=LLM_MODEL,
    api_key=GROQ_API_KEY,
)


# --------------------------------------------------
# Embedding Model
# --------------------------------------------------

Settings.embed_model = HuggingFaceEmbedding(
    model_name=EMBEDDING_MODEL,
)


# --------------------------------------------------
# Global index
# --------------------------------------------------

_index: VectorStoreIndex | None = None


def get_index() -> VectorStoreIndex:

    global _index

    if _index is not None:
        return _index

    if not STORAGE_DIR.exists():
        raise RuntimeError(
            "Storage directory does not exist."
        )

    try:

        storage_context = (
            StorageContext.from_defaults(
                persist_dir=str(STORAGE_DIR)
            )
        )

        _index = load_index_from_storage(
            storage_context
        )

        return _index

    except Exception as exc:

        raise RuntimeError(
            "No valid RAG index found. "
            "Upload a document first."
        ) from exc


def reset_index() -> None:

    global _index

    _index = None


def ask_question(question: str) -> dict:

    index = get_index()

    # --------------------------------------------------
    # Index → Query Engine
    # --------------------------------------------------

    query_engine = index.as_query_engine(
        similarity_top_k=SIMILARITY_TOP_K,
    )

    # --------------------------------------------------
    # Query Engine → Groq
    # --------------------------------------------------

    response = query_engine.query(
        question
    )

    # --------------------------------------------------
    # Collect source nodes
    # --------------------------------------------------

    sources = []

    for node_with_score in response.source_nodes:

        node = node_with_score.node

        file_name = node.metadata.get(
            "file_name",
            "Unknown",
        )

        sources.append(
            {
                "file_name": file_name,
                "text": node.text,
            }
        )

    return {
        "answer": str(response),
        "sources": sources,
    }