"""
Vector Index Module

This module handles embeddings and VectorStoreIndex creation.

Why we need embeddings:
- Convert text into numerical vector representations
- Enable semantic similarity search
- Allow LlamaIndex to find relevant content based on meaning
- Support efficient vector similarity calculations

What they do:
- Take text as input
- Output a fixed-length vector (array of numbers)
- Similar texts have similar vectors
- Used by VectorStoreIndex for retrieval

Embedding concept:
- A vector is a list of numbers representing text
- Dimensions capture semantic meaning
- Text with similar meaning have vectors close in space
- OpenAI embeddings: 1536 dimensions for text-embedding-3-small

VectorStoreIndex concept:
- Stores nodes with their embedding vectors
- Performs similarity search using vector operations
- Returns most similar nodes for a query
- Primary index for RAG systems
"""

from typing import List, Optional
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from loguru import logger

from app.core.config import settings


class EmbeddingModel:
    """
    Wrapper for embedding model configuration.

    Why we need this class:
    - Centralize embedding model configuration
    - Make it easy to switch embedding models
    - Avoid hard-coding model names throughout the codebase
    - Provide consistent interface

    What it does:
    - Initializes the embedding model from configuration
    - Returns a LlamaIndex BaseEmbedding instance
    - Can be used throughout the application
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        embed_batch_size: int = 10,
    ):
        """
        Initialize the embedding model.

        Args:
            model_name: Name of the embedding model (uses config if None)
            api_key: OpenAI API key (uses config if None)
            embed_batch_size: Number of texts to embed at once

        Why these parameters:
        - model_name: Allows different embedding models
          - text-embedding-3-small: Fast, cost-effective (1536 dimensions)
          - text-embedding-3-large: Higher quality (3072 dimensions)
          - text-embedding-ada-002: Legacy model (1536 dimensions)
        - api_key: Required for OpenAI embeddings
        - embed_batch_size: Controls API call efficiency
          - Larger batches = fewer API calls
          - But too large may hit rate limits
          - 10 is a good default balance

        What is OpenAIEmbedding:
        - LlamaIndex wrapper for OpenAI's embedding API
        - Implements BaseEmbedding interface
        - Handles API calls and rate limiting
        - Returns vector arrays
        """

        self.model_name = model_name or settings.embedding_model
        self.api_key = api_key or settings.openai_api_key
        self.embed_batch_size = embed_batch_size

        # 1. Try OpenAI if API key provided
        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                self.embedding_model = OpenAIEmbedding(
                    model=self.model_name,
                    api_key=self.api_key,
                    embed_batch_size=self.embed_batch_size,
                )
                Settings.embed_model = self.embedding_model
                logger.info(f"Initialized OpenAI embedding model: {self.model_name}")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAIEmbedding: {e}")

        # 2. FastEmbed local embeddings (fast, CPU-friendly, no PyTorch needed)
        try:
            from llama_index.embeddings.fastembed import FastEmbedEmbedding
            self.embedding_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
            Settings.embed_model = self.embedding_model
            logger.info("Initialized local FastEmbed embedding model: BAAI/bge-small-en-v1.5")
            return
        except Exception as e:
            logger.warning(f"FastEmbed embedding not loaded: {e}")

        logger.warning(
            "Embedding model not configured. Set OPENAI_API_KEY in .env or install fastembed."
        )
        self.embedding_model = None

    def get_embedding_model(self) -> Optional[BaseEmbedding]:
        """
        Get the embedding model instance.

        Why we need this method:
        - Provide access to the embedding model
        - Used by index creation and query engines
        - Returns BaseEmbedding interface for flexibility

        Returns:
            BaseEmbedding: The embedding model instance, or None if not configured

        What is BaseEmbedding:
        - Abstract interface for embedding models
        - Different implementations (OpenAI, HuggingFace, etc.)
        - Has get_text_embedding() and get_text_embedding_batch() methods
        - Allows swapping embedding models without code changes
        """

        return self.embedding_model

    def get_text_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.

        Why we need this method:
        - Demonstrate how embeddings work
        - Useful for debugging and testing
        - Shows the vector representation

        Args:
            text: Text to embed

        Returns:
            List[float]: Vector representation of the text

        What happens internally:
        1. Send text to OpenAI API
        2. API returns vector array
        3. Return as list of floats

        What does the vector represent?
        - Each dimension captures semantic features
        - Similar texts have similar vectors
        - Distance between vectors indicates similarity
        - Example: "cat" and "dog" have closer vectors than "cat" and "car"
        """

        if self.embedding_model is None:
            raise ValueError(
                "Embedding model not configured. "
                "Set OPENAI_API_KEY in .env file."
            )

        logger.debug(f"Getting embedding for text (length={len(text)})")

        embedding = self.embedding_model.get_text_embedding(text)

        logger.debug(f"Embedding dimension: {len(embedding)}")

        return embedding


class VectorIndex:
    """
    Wrapper for VectorStoreIndex creation and management.

    Why we need this class:
    - Encapsulate VectorStoreIndex creation
    - Provide consistent interface for index operations
    - Handle index configuration
    - Log index operations

    What it does:
    - Creates VectorStoreIndex from nodes
    - Configures index settings
    - Returns index for retrieval
    """

    def __init__(
        self,
        embedding_model: Optional[BaseEmbedding] = None,
    ):
        """
        Initialize the vector index.

        Args:
            embedding_model: Embedding model to use (uses default if None)

        Why we allow custom embedding model:
        - Enables testing with mock embeddings
        - Allows different embedding strategies
        - Supports dependency injection
        """

        if embedding_model:
            Settings.embed_model = embedding_model
        else:
            wrapper = EmbeddingModel()
            if wrapper.embedding_model:
                Settings.embed_model = wrapper.embedding_model

        logger.info("Initialized VectorIndex")

    def create_index(
        self,
        nodes: List,
        show_progress: bool = True,
    ) -> VectorStoreIndex:
        """
        Create a VectorStoreIndex from nodes.

        Why we need this method:
        - Convert nodes into a searchable index
        - Generate embeddings for all nodes
        - Store vectors for similarity search
        - Return index ready for querying

        Args:
            nodes: List of Node objects to index
            show_progress: Whether to show progress bar

        Returns:
            VectorStoreIndex: Created index

        What happens internally:
        1. For each node, generate embedding vector
        2. Store node with its vector in the index
        3. Build data structure for efficient similarity search
        4. Return VectorStoreIndex object

        What is VectorStoreIndex:
        - LlamaIndex's primary index for semantic search
        - Stores nodes with their embedding vectors
        - Performs vector similarity search
        - Returns most similar nodes for a query
        - Supports metadata filtering
        - Can be persisted to disk

        How does it work:
        1. When created, it embeds all nodes
        2. Stores (node, vector) pairs
        3. For a query, embeds the query text
        4. Finds nodes with vectors most similar to query vector
        5. Uses cosine similarity or other distance metrics
        6. Returns top-k most similar nodes

        What would happen if we removed it:
        - No way to perform semantic search
        - Would need to implement vector similarity manually
        - No efficient retrieval mechanism
        - RAG system would not work
        """

        logger.info(f"Creating VectorStoreIndex from {len(nodes)} nodes")

        # Create the index
        # VectorStoreIndex.from_documents() or from_nodes():
        # - Takes nodes as input
        # - Automatically generates embeddings for each node
        # - Builds vector store for similarity search
        # - Returns VectorStoreIndex object
        index = VectorStoreIndex(
            nodes=nodes,
            show_progress=show_progress,
        )

        logger.info(
            f"VectorStoreIndex created successfully "
            f"({len(nodes)} nodes indexed)"
        )

        return index

    def create_index_from_documents(
        self,
        documents: List,
        show_progress: bool = True,
    ) -> VectorStoreIndex:
        """
        Create a VectorStoreIndex from documents (nodes are created automatically).

        Why we need this method:
        - Convenience method for direct document indexing
        - Nodes are created internally
        - Simpler interface when you have documents

        Args:
            documents: List of Document objects
            show_progress: Whether to show progress bar

        Returns:
            VectorStoreIndex: Created index
        """

        logger.info(f"Creating VectorStoreIndex from {len(documents)} documents")

        index = VectorStoreIndex.from_documents(
            documents=documents,
            show_progress=show_progress,
        )

        logger.info(
            f"VectorStoreIndex created successfully "
            f"({len(documents)} documents indexed)"
        )

        return index


# Singleton instances (initialized lazily to handle missing API key)
_embedding_model = None
_vector_index = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create the embedding model singleton."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def get_vector_index() -> VectorIndex:
    """Get or create the vector index singleton."""
    global _vector_index
    if _vector_index is None:
        _vector_index = VectorIndex()
    return _vector_index
