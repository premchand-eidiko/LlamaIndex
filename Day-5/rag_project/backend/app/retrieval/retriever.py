"""
Retriever Module

This module implements the retrieval layer for fetching relevant nodes.

Why we need a retrieval layer:
- Separate retrieval logic from indexing
- Provide consistent interface for different retrieval strategies
- Enable configuration of retrieval parameters
- Support different retrieval modes

What it does:
- Creates retrievers from indexes
- Configures similarity_top_k
- Returns relevant nodes for queries
- Supports different retrieval strategies
"""

from typing import List, Optional
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.vector_stores import MetadataFilters
from loguru import logger

from app.core.config import settings


class RetrieverManager:
    """
    Manager for creating and configuring retrievers.

    Why we need this class:
    - Centralize retriever creation
    - Provide consistent configuration
    - Support different retrieval strategies
    - Enable easy parameter tuning

    What it does:
    - Creates retrievers from indexes
    - Configures retrieval parameters
    - Returns configured retriever instances
    """

    def __init__(
        self,
        similarity_top_k: Optional[int] = None,
    ):
        """
        Initialize the retriever manager.

        Args:
            similarity_top_k: Number of nodes to retrieve (uses config if None)

        Why similarity_top_k:
        - Controls how many nodes are retrieved
        - More nodes = more context but slower
        - Fewer nodes = faster but may miss relevant info
        - Typically 5-10 is a good range
        """

        self.similarity_top_k = similarity_top_k or settings.similarity_top_k

        logger.info(
            f"Initialized RetrieverManager "
            f"(similarity_top_k={self.similarity_top_k})"
        )

    def create_retriever(
        self,
        index: VectorStoreIndex,
        similarity_top_k: Optional[int] = None,
        filters: Optional[MetadataFilters] = None,
    ) -> BaseRetriever:
        """
        Create a retriever from a VectorStoreIndex.

        Why we need this method:
        - Create retriever from index
        - Apply configuration and optional metadata filters
        - Return retriever for querying

        Args:
            index: VectorStoreIndex to create retriever from
            similarity_top_k: Optional override for number of nodes to retrieve
            filters: Optional metadata filters to constrain retrieval

        Returns:
            BaseRetriever: Configured retriever
        """
        top_k = similarity_top_k or self.similarity_top_k
        logger.info(f"Creating retriever with similarity_top_k={top_k}, filters={filters is not None}")

        retriever = index.as_retriever(
            similarity_top_k=top_k,
            filters=filters,
        )

        logger.info("Retriever created successfully")

        return retriever

    def retrieve(
        self,
        retriever: BaseRetriever,
        query: str,
    ) -> List:
        """
        Retrieve nodes for a query.

        Why we need this method:
        - Execute retrieval
        - Return nodes directly
        - Useful for debugging and testing

        Args:
            retriever: Retriever to use
            query: Query string

        Returns:
            List of retrieved nodes with scores

        What happens internally:
        1. Call retriever.retrieve(query)
        2. Retriever embeds the query
        3. Performs similarity search
        4. Returns list of NodeWithScore objects
        5. Each node has a similarity score
        """

        logger.info(f"Retrieving nodes for query: {query}")

        nodes = retriever.retrieve(query)

        logger.info(f"Retrieved {len(nodes)} nodes")

        # Log scores for debugging
        for i, node in enumerate(nodes):
            logger.debug(
                f"  Node {i+1}: score={node.score:.4f}, "
                f"file={node.metadata.get('file_name', 'unknown')}"
            )

        return nodes


# Singleton instance
retriever_manager = RetrieverManager()
