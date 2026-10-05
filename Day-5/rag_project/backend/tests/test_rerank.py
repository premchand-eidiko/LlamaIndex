"""
Phase 9 Test: Node Re-ranking

This script demonstrates and verifies:
1. Re-ranking retrieved candidates by similarity score
2. Filtering with similarity cutoffs
3. Truncating candidates from high-recall top-K (e.g. 10) to high-precision top-N (e.g. 3)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_index.core.schema import TextNode, NodeWithScore, QueryBundle
from app.retrieval.rerank import EnterpriseReranker, RerankerManager, reranker_manager
from app.core.logging import logger


def test_reranking():
    """Test re-ranking with cutoff and top-N sorting."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 9: NODE RE-RANKING")
    logger.info("=" * 60)

    # Create dummy candidate nodes with varying scores
    n1 = NodeWithScore(node=TextNode(text="Chunk 1 (low relevance)"), score=0.45)
    n2 = NodeWithScore(node=TextNode(text="Chunk 2 (high relevance)"), score=0.92)
    n3 = NodeWithScore(node=TextNode(text="Chunk 3 (medium relevance)"), score=0.74)
    n4 = NodeWithScore(node=TextNode(text="Chunk 4 (irrelevant)"), score=0.15)
    n5 = NodeWithScore(node=TextNode(text="Chunk 5 (very high relevance)"), score=0.98)

    candidates = [n1, n2, n3, n4, n5]
    logger.info(f"Input: {len(candidates)} candidate nodes")

    # 1. Test top-N filtering without cutoff
    reranker = EnterpriseReranker(top_n=3)
    results = reranker.postprocess_nodes(candidates, query_bundle=QueryBundle("test query"))

    logger.info(f"Top 3 re-ranked nodes:")
    for i, r in enumerate(results, start=1):
        logger.info(f"   [{i}] Score: {r.score:.2f} | Text: {r.node.get_content()}")

    assert len(results) == 3
    assert results[0].score == 0.98
    assert results[1].score == 0.92
    assert results[2].score == 0.74
    logger.info("   ✓ Candidates correctly sorted in descending order and capped at top-3")

    # 2. Test with similarity cutoff = 0.70
    reranker_cutoff = EnterpriseReranker(top_n=5, similarity_cutoff=0.70)
    cutoff_results = reranker_cutoff.postprocess_nodes(candidates)
    logger.info(f"Re-ranked nodes with cutoff >= 0.70: {len(cutoff_results)} nodes")
    assert len(cutoff_results) == 3
    for r in cutoff_results:
        assert r.score >= 0.70
    logger.info("   ✓ Cutoff successfully dropped chunks below 0.70 score")

    # 3. Test through RerankerManager
    mgr_results = reranker_manager.rerank(candidates, query="leave policy", top_n=2)
    assert len(mgr_results) == 2
    logger.info("   ✓ RerankerManager convenience API functioning properly")

    logger.info("✅ Phase 9 Node Re-ranking test passed successfully!")


if __name__ == "__main__":
    test_reranking()
