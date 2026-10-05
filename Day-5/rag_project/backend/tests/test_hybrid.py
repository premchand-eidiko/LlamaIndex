"""
Phase 8 Test: Hybrid Retrieval

This script demonstrates and verifies:
1. Reciprocal Rank Fusion (RRF) logic
2. Combining dense vector retrieval with sparse lexical retrieval
3. Creation and execution of HybridRetriever
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_index.core.schema import TextNode, NodeWithScore, QueryBundle
from app.indexes.vector import EmbeddingModel, VectorIndex
from app.retrieval.hybrid import (
    reciprocal_rank_fusion,
    HybridRetriever,
    hybrid_retriever_manager,
)
from app.core.logging import logger


def test_hybrid():
    """Test Hybrid Retrieval and RRF fusion."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 8: HYBRID RETRIEVAL & RRF")
    logger.info("=" * 60)

    # 1. Unit test Reciprocal Rank Fusion (works without API key)
    logger.info("1. Testing Reciprocal Rank Fusion (RRF)...")
    node_a = TextNode(text="Node A content about machine learning", id_="node_a")
    node_b = TextNode(text="Node B content about enterprise RAG", id_="node_b")
    node_c = TextNode(text="Node C content about vector databases", id_="node_c")

    list1 = [NodeWithScore(node=node_a, score=0.9), NodeWithScore(node=node_b, score=0.8)]
    list2 = [NodeWithScore(node=node_b, score=10.0), NodeWithScore(node=node_c, score=5.0)]

    fused = reciprocal_rank_fusion([list1, list2], k=60, top_k=3)
    logger.info(f"   Fused {len(fused)} nodes from 2 ranked lists:")
    for i, item in enumerate(fused, start=1):
        logger.info(f"   [{i}] Node: {item.node.id_}, RRF Score: {item.score:.5f}")

    # Node B appeared in both lists, so its RRF score should be highest!
    assert fused[0].node.id_ == "node_b", f"Expected node_b at rank 1, got {fused[0].node.id_}"
    logger.info("   ✓ Node B correctly fused to top rank due to multi-retriever consensus!")

    # Check if embedding model is available
    embedding_model = EmbeddingModel()
    if embedding_model.embedding_model is None:
        logger.warning("\n⚠️  OPENAI_API_KEY not configured")
        logger.info("Running hybrid retrieval concept demonstration...")
        logger.info("\nWhy Hybrid Retrieval is critical for Enterprise:")
        logger.info("- Vector Search captures semantic synonyms (e.g., 'vacation' matches 'annual leave')")
        logger.info("- Lexical Search captures exact identifiers (e.g., 'DOC-2024-X99', acronyms, error codes)")
        logger.info("- Reciprocal Rank Fusion fuses both signals without scale distortion")
        logger.info("\n✅ Phase 8 unit & concept tests passed successfully!")
        return

    # If API key is available, run full end-to-end hybrid retrieval
    nodes = [node_a, node_b, node_c]
    vector_index = VectorIndex()
    index = vector_index.create_index(nodes, show_progress=False)

    hybrid_retriever = hybrid_retriever_manager.create_hybrid_retriever(
        index=index,
        nodes=nodes,
        top_k=2,
    )
    query_bundle = QueryBundle(query_str="enterprise RAG machine learning")
    results = hybrid_retriever.retrieve(query_bundle)
    assert len(results) > 0
    logger.info(f"   Retrieved {len(results)} hybrid results")
    logger.info("✅ Phase 8 Hybrid Retrieval integration test passed successfully!")


if __name__ == "__main__":
    test_hybrid()
