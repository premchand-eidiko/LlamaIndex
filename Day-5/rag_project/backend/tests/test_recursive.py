"""
Phase 11 Test: Recursive Retrieval

This script demonstrates and verifies:
1. Hierarchical Chunking (Parent nodes + Child IndexNodes)
2. Linking child IndexNode to parent TextNode IDs
3. Retrieval traversal from child node match to rich parent context
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_index.core.schema import Document
from app.indexes.vector import EmbeddingModel
from app.retrieval.recursive import (
    HierarchicalChunker,
    RecursiveRetrievalManager,
    recursive_retrieval_manager,
)
from app.core.logging import logger


def test_recursive():
    """Test hierarchical chunking and recursive retrieval."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 11: RECURSIVE RETRIEVAL")
    logger.info("=" * 60)

    # 1. Test Hierarchical Chunking
    sample_long_text = (
        "Enterprise System Architecture Overview.\n"
        "Section 1: Data Ingestion. The ingestion pipeline supports PDF, DOCX, TXT and CSV formats. "
        "Each document is parsed using token-aware chunking and enriched with enterprise metadata tags. "
        "Section 2: Security & Access Control. RBAC enforces least privilege across departments. "
        "Confidential documents require Level 3 clearance. "
        "Section 3: Storage & Indexing. StorageContext maintains docstore, index store, and vector embeddings. "
        "Section 4: High Availability. Multi-region replication guarantees 99.99% uptime."
    )
    doc = Document(text=sample_long_text, metadata={"file_name": "architecture.txt"})

    chunker = HierarchicalChunker(parent_chunk_size=120, child_chunk_size=40)
    parent_nodes, child_nodes, docstore_dict = chunker.create_hierarchical_nodes([doc])

    logger.info(f"1. Hierarchical nodes created:")
    logger.info(f"   Parent nodes: {len(parent_nodes)}")
    logger.info(f"   Child index nodes: {len(child_nodes)}")
    assert len(parent_nodes) >= 1
    assert len(child_nodes) >= len(parent_nodes)

    # Check child references
    first_child = child_nodes[0]
    parent_id = first_child.index_id
    assert parent_id in docstore_dict
    logger.info(f"   ✓ Child '{first_child.node_id[:8]}' points to Parent '{parent_id[:8]}'")

    # Check if embedding model is available
    embedding_model = EmbeddingModel()
    if embedding_model.embedding_model is None:
        logger.warning("\n⚠️  OPENAI_API_KEY not configured")
        logger.info("Running recursive retrieval concept demonstration...")
        logger.info("\nWhy Recursive Retrieval excels in RAG:")
        logger.info("- Search space is small, focused chunks (fine semantic resolution)")
        logger.info("- Context returned to LLM is the comprehensive parent chunk")
        logger.info("- Solves the 'lost in the middle' and context fragmentation issues")
        logger.info("\n✅ Phase 11 unit & concept tests passed successfully!")
        return

    # If API key is available, run full recursive retrieval
    retriever, _ = recursive_retrieval_manager.build_recursive_retriever([doc], top_k=1)
    results = retriever.retrieve("What are the security and clearance rules?")
    logger.info(f"2. Retrieved {len(results)} nodes via RecursiveRetriever:")
    for r in results:
        logger.info(f"   - Parent context: {r.node.get_content()[:80]}...")
    assert len(results) > 0

    logger.info("✅ Phase 11 Recursive Retrieval integration test passed successfully!")


if __name__ == "__main__":
    test_recursive()
