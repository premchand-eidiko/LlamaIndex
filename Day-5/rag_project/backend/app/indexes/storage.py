"""
Storage and Persistence Module

This module handles persistent storage for indexes and documents.

Why we need persistent storage:
- Avoid re-embedding documents on every restart
- Save time and API costs
- Maintain state across application restarts
- Enable incremental updates to indexes

What it does:
- Saves indexes to disk
- Saves document store
- Saves vector store
- Loads previously saved indexes
- Manages storage directory structure

StorageContext concept:
- Manages all storage backends in LlamaIndex
- Coordinates docstore, index_store, vector_store, graph_store
- Provides unified interface for persistence
- Handles serialization and deserialization

Storage components:
- docstore: Stores Document and Node objects
- index_store: Stores index structures and metadata
- vector_store: Stores embedding vectors
- graph_store: Stores graph data (for GraphRAG)
"""

from pathlib import Path
from typing import Optional
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage, Settings
from llama_index.core.storage import StorageContext as BaseStorageContext
from loguru import logger

from app.core.config import settings


class IndexStorage:
    """
    Manager for index persistence using StorageContext.

    Why we need this class:
    - Centralize storage operations
    - Provide clean interface for saving/loading
    - Handle storage directory management
    - Log storage operations

    What it does:
    - Creates StorageContext with appropriate storage backends
    - Saves indexes to disk
    - Loads indexes from disk
    - Manages storage directory structure
    """

    def __init__(
        self,
        storage_dir: Optional[str] = None,
    ):
        """
        Initialize the index storage manager.

        Args:
            storage_dir: Directory for persistent storage (uses config if None)

        Why we need storage_dir:
        - Separate storage from application code
        - Configurable location for different environments
        - Easy backup and migration
        """

        self.storage_dir = Path(storage_dir or settings.storage_dir)

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized IndexStorage with directory: {self.storage_dir}")

    def create_storage_context(self) -> StorageContext:
        """
        Create a StorageContext for persistence.

        Why we need this method:
        - StorageContext is required for index persistence
        - Configures where to store different components
        - Provides unified interface to all storage backends

        Returns:
            StorageContext: Configured storage context

        What is StorageContext:
        - LlamaIndex's storage management interface
        - Coordinates multiple storage backends
        - Handles serialization and deserialization
        - Provides methods to save/load entire index ecosystem

        What does it manage:
        - docstore: Document and Node objects
        - index_store: Index structures and metadata
        - vector_store: Embedding vectors
        - graph_store: Graph data (for GraphRAG)

        How it works:
        1. Each component has its own storage backend
        2. StorageContext coordinates them
        3. When you save an index, it saves all components
        4. When you load, it reconstructs the complete index

        What would happen if we removed it:
        - No way to persist indexes
        - Would need to re-embed on every restart
        - Wasteful of time and API costs
        - No incremental updates possible
        """

        logger.info("Creating StorageContext")

        # Create StorageContext with default storage backends
        # By default, LlamaIndex uses:
        # - SimpleDocumentStore (JSON-based) for docstore
        # - SimpleIndexStore (JSON-based) for index_store
        # - SimpleVectorStore (JSON-based) for vector_store
        from pathlib import Path
        p_dir = Path(self.storage_dir)
        if (p_dir / "docstore.json").exists():
            storage_context = StorageContext.from_defaults(persist_dir=str(p_dir))
            logger.info(f"StorageContext loaded from persist_dir: {p_dir}")
        else:
            storage_context = StorageContext.from_defaults()
            logger.info(f"New StorageContext created (will persist to: {p_dir})")

        return storage_context

    def save_index(
        self,
        index: VectorStoreIndex,
        storage_context: Optional[StorageContext] = None,
    ) -> None:
        """
        Save an index to persistent storage.

        Why we need this method:
        - Persist index to disk
        - Enable loading without re-embedding
        - Save time and API costs on restart

        Args:
            index: VectorStoreIndex to save
            storage_context: StorageContext to use (creates new if None)

        What happens internally:
        1. Create or use provided StorageContext
        2. Call index.storage_context to save
        3. Saves all components (docstore, index_store, vector_store)
        4. Writes to persist_dir on disk

        What gets saved:
        - All Document and Node objects (docstore)
        - Index structure and metadata (index_store)
        - All embedding vectors (vector_store)
        - Enables complete reconstruction of the index
        """

        logger.info(f"Saving index to storage: {self.storage_dir}")
        from pathlib import Path
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        index.storage_context.persist(persist_dir=str(self.storage_dir))
        logger.info("Index saved successfully")

    def load_index(
        self,
        storage_context: Optional[StorageContext] = None,
    ) -> VectorStoreIndex:
        """
        Load an index from persistent storage.

        Why we need this method:
        - Load previously saved index
        - Avoid re-embedding documents
        - Fast application startup

        Args:
            storage_context: StorageContext to use (creates new if None)

        Returns:
            VectorStoreIndex: Loaded index

        What happens internally:
        1. Create or use provided StorageContext
        2. Load all components from disk
        3. Reconstruct the index
        4. Return fully functional index

        What gets loaded:
        - All Document and Node objects from docstore
        - Index structure from index_store
        - All embedding vectors from vector_store
        - Reconstructs complete index ecosystem

        What would happen if we removed it:
        - Would need to re-embed on every startup
        - Slow application startup
        - Wasteful of API costs
        - No persistence between sessions
        """

        logger.info(f"Loading index from storage: {self.storage_dir}")

        from app.indexes.vector import EmbeddingModel
        wrapper = EmbeddingModel()
        if wrapper.embedding_model:
            Settings.embed_model = wrapper.embedding_model

        if storage_context is None:
            storage_context = self.create_storage_context()

        # Load the index
        index = load_index_from_storage(
            storage_context=storage_context,
            embed_model=Settings.embed_model,
        )

        logger.info("Index loaded successfully")

        return index

    def index_exists(self) -> bool:
        """
        Check if a saved index exists in storage.

        Why we need this method:
        - Avoid errors when loading non-existent index
        - Enable conditional loading
        - Support incremental updates

        Returns:
            bool: True if index exists, False otherwise
        """

        # Check if storage directory exists and has content
        if not self.storage_dir.exists():
            return False

        # Check for required storage files
        # LlamaIndex creates specific files:
        # - docstore.json
        # - index_store.json
        # - vector_store.json
        required_files = [
            "docstore.json",
            "index_store.json",
        ]

        for file_name in required_files:
            if not (self.storage_dir / file_name).exists():
                return False

        return True

    def clear_storage(self) -> None:
        """
        Clear all persistent storage.

        Why we need this method:
        - Reset storage completely
        - Force full re-indexing
        - Clean up corrupted storage

        WARNING: This deletes all saved indexes and documents!
        """

        logger.warning(f"Clearing storage directory: {self.storage_dir}")

        # Delete all files in storage directory
        for file_path in self.storage_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                # Recursively delete subdirectories
                for item in file_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        for sub_item in item.iterdir():
                            sub_item.unlink()
                        file_path.rmdir()
                file_path.rmdir()

        logger.info("Storage cleared successfully")


# Singleton instance
index_storage = IndexStorage()
