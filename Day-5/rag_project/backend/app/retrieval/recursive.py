"""
Recursive Retrieval Module (Phase 11)

This module implements hierarchical chunking and recursive retrieval.

Why we need Recursive Retrieval:
- Small chunks (leaf nodes) yield superior embedding similarity search.
- Large chunks (parent nodes) provide richer, coherent context for LLM generation.
- Recursive retrieval embeds small child nodes (or summaries) that reference larger parent nodes.
- During retrieval, small chunks are matched first, and the retriever traverses references to return rich parent context.
"""

from typing import List, Dict, Optional, Tuple
from llama_index.core.schema import TextNode, IndexNode, NodeWithScore, QueryBundle, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.retrievers import RecursiveRetriever, BaseRetriever
from loguru import logger

from app.core.config import settings


class HierarchicalChunker:
    """
    Splits documents into parent-child node hierarchies.
    """

    def __init__(
        self,
        parent_chunk_size: int = 1024,
        child_chunk_size: int = 256,
        overlap: int = 40,
    ):
        self.parent_splitter = SentenceSplitter(chunk_size=parent_chunk_size, chunk_overlap=overlap)
        self.child_splitter = SentenceSplitter(chunk_size=child_chunk_size, chunk_overlap=overlap // 2)
        logger.info(f"Initialized HierarchicalChunker (parent={parent_chunk_size}, child={child_chunk_size})")

    def create_hierarchical_nodes(
        self,
        documents: List[Document],
    ) -> Tuple[List[TextNode], List[IndexNode], Dict[str, TextNode]]:
        """
        Create parent nodes and child IndexNodes pointing to parents.

        Returns:
            Tuple of (parent_nodes, child_index_nodes, docstore_dict)
        """
        parent_nodes: List[TextNode] = self.parent_splitter.get_nodes_from_documents(documents)
        child_index_nodes: List[IndexNode] = []
        docstore_dict: Dict[str, TextNode] = {}

        for p_idx, parent_node in enumerate(parent_nodes):
            parent_id = parent_node.node_id
            docstore_dict[parent_id] = parent_node

            # Split parent into smaller child chunks
            child_text_nodes = self.child_splitter.get_nodes_from_documents([parent_node])
            for c_idx, child in enumerate(child_text_nodes):
                # Create IndexNode with index_id pointing to parent
                index_node = IndexNode(
                    text=child.get_content(),
                    index_id=parent_id,
                    metadata={
                        **parent_node.metadata,
                        "parent_id": parent_id,
                        "child_idx": c_idx,
                    },
                )
                child_index_nodes.append(index_node)

        logger.info(
            f"Created hierarchy: {len(parent_nodes)} parent nodes, "
            f"{len(child_index_nodes)} child index nodes"
        )
        return parent_nodes, child_index_nodes, docstore_dict


class RecursiveRetrievalManager:
    """
    Manager for setting up and querying recursive retrievers.
    """

    def __init__(self, top_k: Optional[int] = None):
        self.top_k = top_k or settings.similarity_top_k
        self.chunker = HierarchicalChunker()

    def build_recursive_retriever(
        self,
        documents: List[Document],
        top_k: Optional[int] = None,
    ) -> Tuple[BaseRetriever, StorageContext]:
        """
        Builds VectorStoreIndex on child nodes and links RecursiveRetriever to parent docstore.
        """
        k = top_k or self.top_k
        parent_nodes, child_nodes, docstore_dict = self.chunker.create_hierarchical_nodes(documents)

        # Build docstore containing all parents
        docstore = SimpleDocumentStore()
        docstore.add_documents(parent_nodes)

        storage_context = StorageContext.from_defaults(docstore=docstore)

        # Index only the child nodes for fine-grained retrieval
        index = VectorStoreIndex(child_nodes, storage_context=storage_context)

        # Create base retriever on the child index
        base_retriever = index.as_retriever(similarity_top_k=k)

        # Wrap in RecursiveRetriever to resolve IndexNode -> Parent TextNode
        recursive_retriever = RecursiveRetriever(
            "root",
            retriever_dict={"root": base_retriever},
            node_dict=docstore_dict,
            verbose=False,
        )

        logger.info(f"Successfully built RecursiveRetriever (top_k={k})")
        return recursive_retriever, storage_context


# Global instance
recursive_retrieval_manager = RecursiveRetrievalManager()
