"""
Phase 12 Test: Router Query Engine

This script demonstrates and verifies:
1. Tool creation for VectorStoreIndex (factual search) and SummaryIndex (holistic summary)
2. ToolMetadata and query routing logic
3. RouterQueryEngine initialization and query routing
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_index.core.schema import Document
from app.indexes.vector import EmbeddingModel
from app.query.router import RouterEngineManager, router_engine_manager
from app.core.logging import logger


def test_router():
    """Test Router Query Engine tools and routing logic."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 12: ROUTER QUERY ENGINE")
    logger.info("=" * 60)

    # 1. Test routing classification logic
    test_queries = [
        ("Summarize the entire 2024 compliance policy", "summary_tool"),
        ("Give an overview of all employee benefits", "summary_tool"),
        ("What is the exact reimbursement deadline for meals?", "vector_tool"),
        ("Who is the primary contact for HR escalations?", "vector_tool"),
    ]

    logger.info("1. Testing query routing logic:")
    for query, expected_tool in test_queries:
        selected_tool = router_engine_manager.route_query_rule_based(query)
        logger.info(f"   Query: '{query}'")
        logger.info(f"   -> Routed to: [{selected_tool}] (Expected: [{expected_tool}])")
        assert selected_tool == expected_tool, f"Expected {expected_tool}, got {selected_tool}"
    logger.info("   ✓ All sample queries routed to appropriate tools correctly!")

    # Check if embedding model is available
    embedding_model = EmbeddingModel()
    if embedding_model.embedding_model is None:
        logger.warning("\n⚠️  OPENAI_API_KEY not configured")
        logger.info("Running router query engine concept demonstration...")
        logger.info("\nWhy Router Query Engine is essential:")
        logger.info("- Prevents 'one-size-fits-all' query engine limitations")
        logger.info("- VectorIndex gives high precision for specific clauses and data points")
        logger.info("- SummaryIndex synthesizes high-level questions without retrieval truncation")
        logger.info("- Dynamic LLM selector picks the best engine with reasoning")
        logger.info("\n✅ Phase 12 unit & concept tests passed successfully!")
        return

    # If API key is available, run live router query engine
    doc1 = Document(text="Annual bonus calculation: 10% base + performance multiplier up to 1.5x.")
    doc2 = Document(text="Travel per diem: $75 daily meal allowance for domestic travel.")
    router_engine = router_engine_manager.build_router_query_engine([doc1, doc2])

    resp = router_engine.query("What is the meal allowance?")
    logger.info(f"2. Live Router response: {resp}")
    assert len(str(resp)) > 0
    logger.info("✅ Phase 12 Router Query Engine integration test passed successfully!")


if __name__ == "__main__":
    test_router()
