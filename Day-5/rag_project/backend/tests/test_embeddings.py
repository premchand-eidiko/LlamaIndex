"""
Test script for embeddings and VectorStoreIndex.

This script demonstrates:
1. Creating embeddings for text
2. Building a VectorStoreIndex from nodes
3. Understanding the embedding dimension
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.pipeline import ingestion_pipeline
from app.indexes.vector import EmbeddingModel, VectorIndex, get_embedding_model, get_vector_index
from app.core.config import settings
from app.core.logging import logger


def test_embeddings_and_index():
    """
    Test embeddings and VectorStoreIndex creation.
    """

    logger.info("=" * 60)
    logger.info("TESTING EMBEDDINGS AND VECTORSTOREINDEX")
    logger.info("=" * 60)

    # Create sample documents
    sample_doc_path = Path("data/documents/sample2.txt")

    sample_content = """
ARTIFICIAL INTELLIGENCE POLICY

1. PURPOSE
This policy establishes guidelines for the ethical use of artificial intelligence
within our organization.

2. AI PRINCIPLES
We are committed to developing and using AI that is:
- Fair and unbiased
- Transparent and explainable
- Privacy-preserving
- Secure and reliable

3. USE CASES
Approved AI use cases include:
- Document analysis and summarization
- Customer service chatbots
- Predictive analytics
- Process automation

4. GOVERNANCE
All AI projects must be reviewed by the AI Ethics Committee before deployment.
Regular audits are required to ensure compliance with this policy.
"""

    # Create the sample file
    sample_doc_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sample_doc_path, "w") as f:
        f.write(sample_content)

    logger.info(f"Created sample document: {sample_doc_path}")

    # Test embedding model
    logger.info("\n" + "=" * 60)
    logger.info("TESTING EMBEDDING MODEL")
    logger.info("=" * 60)

    test_text = "Artificial intelligence should be used ethically."

    logger.info(f"Test text: '{test_text}'")

    # Try to initialize embedding model
    try:
        embedding_model = EmbeddingModel()
        if embedding_model.embedding_model is None:
            logger.warning("\n⚠️  OPENAI_API_KEY not configured")
            logger.info("Skipping embedding test")
            logger.info("\nTo enable this test:")
            logger.info("1. Copy .env.example to .env")
            logger.info("2. Add your OpenAI API key to .env")
            logger.info("3. Run the test again")
            logger.info("\n" + "=" * 60)
            logger.info("DEMONSTRATING EMBEDDING CONCEPT (without API call)")
            logger.info("=" * 60)
            logger.info("What embeddings do:")
            logger.info("- Convert text to numerical vectors")
            logger.info("- Example: 'AI ethics' → [0.123, -0.456, 0.789, ...]")
            logger.info("- Similar texts have similar vectors")
            logger.info("- Enable semantic search by meaning, not keywords")
            logger.info(f"\nDefault embedding model: {settings.embedding_model}")
            logger.info(f"Expected dimension: {settings.embedding_dimension}")
            logger.info("\nContinuing with document ingestion demo...")
            return

        # Get embedding for the text
        embedding = embedding_model.get_text_embedding(test_text)

        logger.info(f"\n✅ Successfully generated embedding")
        logger.info(f"   Embedding dimension: {len(embedding)}")
        logger.info(f"   First 5 values: {embedding[:5]}")
        logger.info(f"   Last 5 values: {embedding[-5:]}")

    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        logger.error("Make sure OPENAI_API_KEY is set in .env file")
        logger.info("\n⚠️  Skipping embedding test - API key not configured")
        logger.info("To enable this test:")
        logger.info("1. Copy .env.example to .env")
        logger.info("2. Add your OpenAI API key to .env")
        logger.info("3. Run the test again")
        return

    # Ingest document and create nodes
    logger.info("\n" + "=" * 60)
    logger.info("INGESTING DOCUMENT FOR INDEXING")
    logger.info("=" * 60)

    extra_metadata = {
        "department": "IT",
        "document_category": "policy",
        "access_level": "internal",
    }

    try:
        nodes = ingestion_pipeline.ingest_file(
            str(sample_doc_path),
            extra_metadata=extra_metadata,
        )

        logger.info(f"\n✅ Successfully ingested document")
        logger.info(f"   Total nodes created: {len(nodes)}")

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return

    # Create VectorStoreIndex
    logger.info("\n" + "=" * 60)
    logger.info("CREATING VECTORSTOREINDEX")
    logger.info("=" * 60)

    try:
        vector_index = VectorIndex()
        index = vector_index.create_index(nodes)

        logger.info(f"\n✅ Successfully created VectorStoreIndex")
        logger.info(f"   Index type: {type(index).__name__}")
        logger.info(f"   Index is ready for querying")

        # Explain what happens next
        logger.info("\n" + "=" * 60)
        logger.info("WHAT HAPPENS NEXT")
        logger.info("=" * 60)
        logger.info("1. The VectorStoreIndex has embedded all nodes")
        logger.info("2. Each node now has a vector representation")
        logger.info("3. When you query, the index will:")
        logger.info("   - Embed your query text")
        logger.info("   - Find nodes with similar vectors")
        logger.info("   - Return the most relevant nodes")
        logger.info("\nThis enables semantic search based on meaning, not keywords!")

        return index

    except Exception as e:
        logger.error(f"❌ Index creation failed: {e}")
        logger.error("This usually means OPENAI_API_KEY is not set")
        logger.info("\n⚠️  Skipping index creation - API key not configured")
        logger.info("To enable this test:")
        logger.info("1. Copy .env.example to .env")
        logger.info("2. Add your OpenAI API key to .env")
        logger.info("3. Run the test again")
        return


if __name__ == "__main__":
    test_embeddings_and_index()
