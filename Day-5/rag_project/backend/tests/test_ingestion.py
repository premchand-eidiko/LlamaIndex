"""
Test script for document ingestion pipeline.

This script demonstrates the ingestion pipeline working with sample documents.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.pipeline import ingestion_pipeline
from app.core.logging import logger


def test_ingestion():
    """
    Test the ingestion pipeline with a sample text file.
    """

    logger.info("=" * 60)
    logger.info("TESTING DOCUMENT INGESTION PIPELINE")
    logger.info("=" * 60)

    # Create a sample document
    sample_doc_path = Path("data/documents/sample.txt")

    # Create sample content
    sample_content = """
EMPLOYEE HANDBOOK - SAMPLE CONTENT

1. COMPANY OVERVIEW
Welcome to our company! We are committed to creating a positive work environment
where employees can thrive and grow.

2. WORK FROM HOME POLICY
Employees may work remotely up to 3 days per week. Remote work arrangements
must be approved by the employee's manager and HR department.

3. LEAVE POLICY
Full-time employees are entitled to 20 days of paid annual leave per year.
Additional leave may be granted for medical reasons, family emergencies,
or other special circumstances with manager approval.

4. BENEFITS
We offer comprehensive benefits including health insurance, retirement plans,
and professional development opportunities.

5. CODE OF CONDUCT
All employees are expected to maintain high standards of professionalism
and integrity in their work.
"""

    # Create the sample file
    sample_doc_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sample_doc_path, "w") as f:
        f.write(sample_content)

    logger.info(f"Created sample document: {sample_doc_path}")

    # Test ingestion with metadata
    extra_metadata = {
        "department": "HR",
        "document_category": "handbook",
        "access_level": "internal",
    }

    logger.info("\n" + "=" * 60)
    logger.info("INGESTING DOCUMENT")
    logger.info("=" * 60)

    try:
        nodes = ingestion_pipeline.ingest_file(
            str(sample_doc_path),
            extra_metadata=extra_metadata,
        )

        logger.info(f"\n✅ Successfully ingested document")
        logger.info(f"   Total nodes created: {len(nodes)}")

        # Display first node as example
        if nodes:
            logger.info(f"\n📄 First node example:")
            logger.info(f"   Text length: {len(nodes[0].text)} characters")
            logger.info(f"   Metadata: {nodes[0].metadata}")

        return nodes

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise


if __name__ == "__main__":
    test_ingestion()
