"""
Test script for StorageContext and persistence.

This script demonstrates:
1. Creating a StorageContext
2. Saving an index to disk
3. Loading an index from disk
4. Understanding what gets persisted
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.pipeline import ingestion_pipeline
from app.indexes.vector import EmbeddingModel, VectorIndex
from app.indexes.storage import IndexStorage, index_storage
from app.core.config import settings
from app.core.logging import logger


def test_storage():
    """
    Test StorageContext and index persistence.
    """

    logger.info("=" * 60)
    logger.info("TESTING STORAGECONTEXT AND PERSISTENCE")
    logger.info("=" * 60)

    # Check if embedding model is available
    embedding_model = EmbeddingModel()
    if embedding_model.embedding_model is None:
        logger.warning("\n⚠️  OPENAI_API_KEY not configured")
        logger.info("Skipping storage test (requires embeddings)")
        logger.info("\nTo enable this test:")
        logger.info("1. Copy .env.example to .env")
        logger.info("2. Add your OpenAI API key to .env")
        logger.info("3. Run the test again")
        logger.info("\n" + "=" * 60)
        logger.info("DEMONSTRATING STORAGE CONCEPT (without API call)")
        logger.info("=" * 60)
        logger.info("What StorageContext does:")
        logger.info("- Manages persistent storage for indexes")
        logger.info("- Saves:")
        logger.info("  * docstore: Documents and Nodes")
        logger.info("  * index_store: Index structures")
        logger.info("  * vector_store: Embedding vectors")
        logger.info("- Enables loading without re-embedding")
        logger.info(f"\nStorage directory: {settings.storage_dir}")
        logger.info("\nExample storage flow:")
        logger.info("1. Ingest documents → Create nodes")
        logger.info("2. Generate embeddings → Create index")
        logger.info("3. Save with StorageContext → Persist to disk")
        logger.info("4. Load from StorageContext → Skip re-embedding")
        logger.info("\nBenefits:")
        logger.info("- Fast application startup")
        logger.info("- Save API costs (no re-embedding)")
        logger.info("- Enable incremental updates")
        return

    # Create sample document
    sample_doc_path = Path("data/documents/sample3.txt")

    sample_content = """
DATA RETENTION POLICY

1. OVERVIEW
This policy defines how long we retain different types of data.

2. RETENTION PERIODS
- Employee records: 7 years after termination
- Financial records: 10 years
- Customer data: 5 years after account closure
- Project documentation: 3 years after project completion

3. DATA DELETION
When retention period expires, data must be:
- Securely deleted from production systems
- Archived for legal requirements if needed
- Logged in the deletion registry

4. COMPLIANCE
All data retention practices must comply with:
- GDPR (for EU data)
- CCPA (for California residents)
- Industry-specific regulations
"""

    sample_doc_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sample_doc_path, "w") as f:
        f.write(sample_content)

    logger.info(f"Created sample document: {sample_doc_path}")

    # Ingest document
    logger.info("\n" + "=" * 60)
    logger.info("STEP 1: INGESTING DOCUMENT")
    logger.info("=" * 60)

    extra_metadata = {
        "department": "Legal",
        "document_category": "policy",
        "access_level": "confidential",
    }

    nodes = ingestion_pipeline.ingest_file(
        str(sample_doc_path),
        extra_metadata=extra_metadata,
    )

    logger.info(f"✅ Ingested {len(nodes)} nodes")

    # Create index
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: CREATING VECTORSTOREINDEX")
    logger.info("=" * 60)

    vector_index = VectorIndex()
    index = vector_index.create_index(nodes)

    logger.info(f"✅ Created VectorStoreIndex")

    # Create StorageContext
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: CREATING STORAGECONTEXT")
    logger.info("=" * 60)

    storage_context = index_storage.create_storage_context()

    logger.info(f"✅ Created StorageContext")
    logger.info(f"   Storage directory: {index_storage.storage_dir}")

    # Save index
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: SAVING INDEX TO STORAGE")
    logger.info("=" * 60)

    index_storage.save_index(index, storage_context)

    logger.info("✅ Index saved to disk")

    # List saved files
    logger.info("\n" + "=" * 60)
    logger.info("SAVED FILES")
    logger.info("=" * 60)

    storage_files = list(index_storage.storage_dir.iterdir())
    for file_path in storage_files:
        file_size = file_path.stat().st_size if file_path.is_file() else 0
        logger.info(f"   {file_path.name} ({file_size} bytes)")

    # Check if index exists
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: CHECKING IF INDEX EXISTS")
    logger.info("=" * 60)

    exists = index_storage.index_exists()
    logger.info(f"✅ Index exists: {exists}")

    # Load index
    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: LOADING INDEX FROM STORAGE")
    logger.info("=" * 60)

    loaded_index = index_storage.load_index()

    logger.info("✅ Index loaded from disk")
    logger.info(f"   Index type: {type(loaded_index).__name__}")

    # Explain benefits
    logger.info("\n" + "=" * 60)
    logger.info("BENEFITS OF PERSISTENCE")
    logger.info("=" * 60)
    logger.info("1. Fast startup: No need to re-embed documents")
    logger.info("2. Cost savings: No repeated API calls to embedding service")
    logger.info("3. Consistency: Same index across restarts")
    logger.info("4. Incremental updates: Add new documents without rebuilding")
    logger.info("\n" + "=" * 60)
    logger.info("STORAGE STRUCTURE")
    logger.info("=" * 60)
    logger.info("docstore.json:")
    logger.info("  - Contains all Document and Node objects")
    logger.info("  - Preserves text content and metadata")
    logger.info("\nindex_store.json:")
    logger.info("  - Contains index structure and metadata")
    logger.info("  - Enables index reconstruction")
    logger.info("\nvector_store.json:")
    logger.info("  - Contains all embedding vectors")
    logger.info("  - Pre-computed vectors for fast loading")

    return loaded_index


if __name__ == "__main__":
    test_storage()
