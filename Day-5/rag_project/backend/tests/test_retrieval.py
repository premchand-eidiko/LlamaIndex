"""
Phase 6 Test: Vector Retrieval

This script demonstrates and verifies:
1. Creating a retriever from a VectorStoreIndex
2. Configuring similarity_top_k
3. Executing similarity search for queries
4. Inspecting retrieved nodes and similarity scores
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.pipeline import ingestion_pipeline
from app.indexes.vector import EmbeddingModel, VectorIndex
from app.retrieval.retriever import RetrieverManager, retriever_manager
from app.core.config import settings
from app.core.logging import logger


def test_retrieval():
    """Test retrieval layer with VectorStoreIndex."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 6: VECTOR RETRIEVAL LAYER")
    logger.info("=" * 60)

    # Check if embedding model is available
    embedding_model = EmbeddingModel()
    if embedding_model.embedding_model is None:
        logger.warning("\n⚠️  OPENAI_API_KEY not configured")
        logger.info("Running retrieval concept demonstration (without API calls)...")
        logger.info("\nWhat Retriever does:")
        logger.info("- Converts user query into an embedding vector")
        logger.info("- Queries the vector store using cosine similarity")
        logger.info(f"- Returns top-K most relevant nodes (top_k={settings.similarity_top_k})")
        logger.info("- Supplies similarity score and source metadata for each node")
        logger.info("\nRetriever API methods:")
        logger.info("- retriever_manager.create_retriever(index, similarity_top_k=5)")
        logger.info("- retriever_manager.retrieve(retriever, 'What is the leave policy?')")
        logger.info("\n✅ Phase 6 concept test completed successfully.")
        return

    # If API key is available, run end-to-end test
    sample_doc_path = Path("data/documents/sample.txt")
    if not sample_doc_path.exists():
        sample_doc_path.parent.mkdir(parents=True, exist_ok=True)
        sample_doc_path.write_text(
            "Company Leave Policy: Full-time employees receive 20 days paid annual leave. "
            "Remote work policy allows up to 3 days remote per week with manager approval."
        )

    logger.info("1. Ingesting test document...")
    nodes = ingestion_pipeline.ingest_file(
        str(sample_doc_path),
        department="HR",
        document_category="policy",
    )
    logger.info(f"   Created {len(nodes)} nodes")

    logger.info("2. Creating VectorStoreIndex...")
    vector_index = VectorIndex()
    index = vector_index.create_index(nodes, show_progress=False)

    logger.info("3. Initializing RetrieverManager...")
    manager = RetrieverManager(similarity_top_k=2)
    retriever = manager.create_retriever(index)

    query = "How many days of annual leave do employees get?"
    logger.info(f"4. Querying retriever: '{query}'...")
    results = manager.retrieve(retriever, query)

    logger.info(f"   Retrieved {len(results)} nodes:")
    for i, node_with_score in enumerate(results, start=1):
        logger.info(f"   [{i}] Score: {node_with_score.score:.4f}")
        logger.info(f"       Text: {node_with_score.node.get_content()[:100]}...")
        logger.info(f"       File: {node_with_score.node.metadata.get('file_name')}")

    assert len(results) > 0, "Retrieval should return at least 1 node"
    logger.info("✅ Phase 6 Vector Retrieval test passed successfully!")


if __name__ == "__main__":
    test_retrieval()
