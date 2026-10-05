"""
Phase 10 Test: Query Transformation

This script demonstrates and verifies:
1. HyDE (Hypothetical Document Embeddings) generation
2. Query Rewriting and expansion
3. Sub-Question decomposition
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.query.transform import QueryTransformer, query_transformer
from app.core.logging import logger


def test_transform():
    """Test query transformation techniques."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 10: QUERY TRANSFORMATION")
    logger.info("=" * 60)

    # 1. HyDE Test
    query = "What is the policy for maternal and parental leaves?"
    logger.info(f"Original Query: '{query}'")
    hyde_doc = query_transformer.generate_hypothetical_document(query)
    logger.info(f"1. HyDE Hypothetical Document Generated:\n   \"{hyde_doc}\"")
    assert len(hyde_doc) > 0

    # 2. Query Rewriting Test
    short_query = "wfh limit"
    rewritten = query_transformer.rewrite_query(short_query)
    logger.info(f"2. Query Rewriting: '{short_query}' -> '{rewritten}'")
    assert len(rewritten) > len(short_query)

    # 3. Sub-Question Decomposition Test
    complex_query = "What is the annual leave allowance and how does remote work approval work?"
    sub_questions = query_transformer.decompose_query(complex_query)
    logger.info(f"3. Decomposed Query into {len(sub_questions)} sub-questions:")
    for i, sq in enumerate(sub_questions, start=1):
        logger.info(f"   [{i}] {sq}")
    assert len(sub_questions) >= 2

    logger.info("✅ Phase 10 Query Transformation test passed successfully!")


if __name__ == "__main__":
    test_transform()
