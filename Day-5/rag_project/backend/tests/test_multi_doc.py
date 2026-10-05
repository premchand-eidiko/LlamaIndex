"""
Phase 13 Test: Multi-Document Querying

This script demonstrates and verifies:
1. Document registration with metadata and summaries
2. Building per-document QueryEngineTools
3. Cross-document synthesis and comparison
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.indexes.vector import EmbeddingModel
from app.query.multi_doc import MultiDocumentManager, multi_doc_manager
from app.core.logging import logger


def test_multi_doc():
    """Test multi-document registration and querying."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 13: MULTI-DOCUMENT QUERYING")
    logger.info("=" * 60)

    mgr = MultiDocumentManager()

    # Register two corporate documents
    q1_doc = mgr.register_document(
        doc_id="report_q1",
        title="2024 Q1 Financial Report",
        summary="Contains Q1 financial metrics, revenue of $10M, and cloud ARR.",
        text_content="Q1 2024 Results: Total revenue reached $10 million with 25% YoY growth. Cloud ARR was $4.5 million.",
    )

    q2_doc = mgr.register_document(
        doc_id="report_q2",
        title="2024 Q2 Financial Report",
        summary="Contains Q2 financial metrics, revenue of $14M, and cloud ARR.",
        text_content="Q2 2024 Results: Total revenue surged to $14 million with 40% YoY growth. Cloud ARR climbed to $6.8 million.",
    )

    logger.info(f"1. Registered documents: {len(mgr.documents)}")
    assert len(mgr.documents) == 2
    assert "report_q1" in mgr.documents
    assert "report_q2" in mgr.documents

    # Cross-document comparison query
    query = "Compare total revenue between Q1 and Q2"
    comparison = mgr.compare_documents_simple(["report_q1", "report_q2"], query)
    logger.info(f"2. Cross-document extraction results:")
    for doc_title, text in comparison.items():
        logger.info(f"   [{doc_title}]: {text}")
    assert len(comparison) == 2

    # Check if embedding model is available
    embedding_model = EmbeddingModel()
    if embedding_model.embedding_model is None:
        logger.warning("\n⚠️  OPENAI_API_KEY not configured")
        logger.info("Running multi-document concept demonstration...")
        logger.info("\nWhy Multi-Document Architecture is needed:")
        logger.info("- Encapsulates each document with its own dedicated index")
        logger.info("- Tools provide clear summaries to LLM for routing")
        logger.info("- Enables accurate comparison and synthesis without cross-document chunk pollution")
        logger.info("\n✅ Phase 13 unit & concept tests passed successfully!")
        return

    # If API key is available, build tools and index
    tools = mgr.build_document_tools()
    assert len(tools) == 2
    logger.info(f"3. Built {len(tools)} document QueryEngineTools successfully")
    logger.info("✅ Phase 13 Multi-Document Querying integration test passed successfully!")


if __name__ == "__main__":
    test_multi_doc()
