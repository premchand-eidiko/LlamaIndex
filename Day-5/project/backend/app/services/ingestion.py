from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings

from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from app.config import (
    DOCUMENTS_DIR,
    STORAGE_DIR,
    GROQ_API_KEY,
    LLM_MODEL,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
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
# Node Parser
# --------------------------------------------------

splitter = SentenceSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)


def ingest_documents() -> VectorStoreIndex:
    """
    Load documents → create nodes → create embeddings
    → build VectorStoreIndex → persist index.
    """

    documents = SimpleDirectoryReader(
        input_dir=str(DOCUMENTS_DIR),
        recursive=True,
    ).load_data()

    if not documents:
        raise ValueError(
            "No documents found. Upload at least one document."
        )

    print(
        f"Loaded {len(documents)} document(s)."
    )

    # Documents → Nodes
    nodes = splitter.get_nodes_from_documents(
        documents
    )

    print(
        f"Created {len(nodes)} nodes."
    )

    # Nodes → VectorStoreIndex
    index = VectorStoreIndex(
        nodes
    )

    # Persist index
    index.storage_context.persist(
        persist_dir=str(STORAGE_DIR)
    )

    print(
        f"Index persisted to: {STORAGE_DIR}"
    )

    return index