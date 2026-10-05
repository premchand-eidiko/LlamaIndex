"""
Phase 7 Test: Metadata Filtering

This script demonstrates and verifies:
1. Creating single and combined metadata filters (FilterManager)
2. Creating department-specific and category-specific filters
3. Applying filters during retrieval to restrict results by metadata
4. Verifying that only nodes matching metadata conditions are returned
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.pipeline import ingestion_pipeline
from app.indexes.vector import EmbeddingModel, VectorIndex
from app.retrieval.retriever import RetrieverManager
from app.retrieval.filters import FilterManager, filter_manager
from app.core.logging import logger


def test_filters():
    """Test metadata filters and filtered retrieval."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 7: METADATA FILTERING")
    logger.info("=" * 60)

    # Unit test filter creation (works without API key)
    logger.info("1. Testing FilterManager creation...")
    fm = FilterManager()

    single_filter = fm.create_filter("department", "HR")
    assert single_filter.key == "department"
    assert single_filter.value == "HR"
    logger.info(f"   Created single filter: {single_filter.key} == {single_filter.value}")

    dept_filters = fm.create_department_filter("Finance")
    assert len(dept_filters.filters) == 1
    logger.info(f"   Created department filter: {dept_filters.filters[0].key} == {dept_filters.filters[0].value}")

    cat_filters = fm.create_category_filter("policy")
    assert len(cat_filters.filters) == 1
    logger.info(f"   Created category filter: {cat_filters.filters[0].key} == {cat_filters.filters[0].value}")

    combined = fm.create_filters({"department": "HR", "access_level": "internal"}, condition="and")
    assert len(combined.filters) == 2
    logger.info(f"   Created combined AND filters: {len(combined.filters)} conditions")

    # Check if embedding model is available for live index test
    embedding_model = EmbeddingModel()
    if embedding_model.embedding_model is None:
        logger.warning("\n⚠️  OPENAI_API_KEY not configured")
        logger.info("Running filtering concept demonstration (without API calls)...")
        logger.info("\nWhat Metadata Filtering does:")
        logger.info("- Filters candidate nodes based on structured document metadata")
        logger.info("- Allows targeted search: department='HR', category='policy'")
        logger.info("- Supports AND / OR boolean logic")
        logger.info("- Reduces false positives and enforces access control")
        logger.info("\n✅ Phase 7 unit & concept tests passed successfully!")
        return

    # Live index test with 2 documents of different departments
    hr_doc_path = Path("data/documents/hr_sample.txt")
    finance_doc_path = Path("data/documents/finance_sample.txt")

    hr_doc_path.parent.mkdir(parents=True, exist_ok=True)
    hr_doc_path.write_text("HR Guide: Annual vacation is 20 days. Health insurance starts day 1.")
    finance_doc_path.write_text("Finance Guide: Travel reimbursement forms must be submitted within 30 days.")

    hr_nodes = ingestion_pipeline.ingest_file(str(hr_doc_path), department="HR", document_category="handbook")
    finance_nodes = ingestion_pipeline.ingest_file(str(finance_doc_path), department="Finance", document_category="handbook")

    all_nodes = hr_nodes + finance_nodes
    vector_index = VectorIndex()
    index = vector_index.create_index(all_nodes, show_progress=False)

    rm = RetrieverManager(similarity_top_k=5)

    # Retrieve with HR filter only
    hr_filter = fm.create_department_filter("HR")
    hr_retriever = rm.create_retriever(index, filters=hr_filter)
    results = rm.retrieve(hr_retriever, "vacation or travel rules")

    logger.info(f"2. Retrieved {len(results)} nodes with department='HR' filter:")
    for r in results:
        dept = r.node.metadata.get("department")
        logger.info(f"   - Match: {r.node.metadata.get('file_name')} (dept={dept})")
        assert dept == "HR", f"Expected department 'HR', got '{dept}'"

    logger.info("✅ Phase 7 Metadata Filtering integration test passed successfully!")


if __name__ == "__main__":
    test_filters()
