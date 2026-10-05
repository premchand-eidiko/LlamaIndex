"""
Phase 14 Test: GraphRAG / Knowledge Graph

This script demonstrates and verifies:
1. Triplet creation (subject, relation, object)
2. Adding triplets to KnowledgeGraphStore
3. Multi-hop Breadth-First-Search traversal
4. Querying network subgraph around an entity
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph.knowledge_graph import (
    GraphTriplet,
    KnowledgeGraphStore,
    KnowledgeGraphManager,
    kg_manager,
)
from app.core.logging import logger


def test_graph():
    """Test GraphRAG extraction and multi-hop traversal."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 14: GRAPHRAG / KNOWLEDGE GRAPH")
    logger.info("=" * 60)

    # 1. Test direct Knowledge Graph Store
    store = KnowledgeGraphStore()
    store.add_triplet("Alice", "manages", "Security Team")
    store.add_triplet("Security Team", "part_of", "IT Operations")
    store.add_triplet("IT Operations", "requires", "Zero Trust Policy")
    store.add_triplet("Alice", "reports_to", "CTO")

    logger.info(f"1. Entities in graph: {len(store.entities)}")
    assert "alice" in store.entities
    assert "security team" in store.entities

    # Multi-hop search from 'alice'
    paths = store.multi_hop_search("alice", max_depth=3)
    logger.info(f"2. Multi-hop traversal paths from 'alice':")
    for i, path in enumerate(paths, start=1):
        logger.info(f"   [{i}] {' '.join(path)}")
    assert len(paths) >= 2

    # 2. Test KnowledgeGraphManager extraction
    enterprise_text = (
        "Alice manages Security Team\n"
        "Security Team requires Zero Trust Policy\n"
        "Department: Engineering\n"
        "Location: Head Office"
    )
    extracted = kg_manager.extract_triplets_from_text(enterprise_text)
    logger.info(f"3. Extracted {len(extracted)} triplets from enterprise text")
    assert len(extracted) >= 2

    # Query network subgraph
    query_result = kg_manager.query_graph("alice")
    logger.info(f"4. Query subgraph for 'alice': {query_result}")
    assert query_result["paths_found"] >= 1

    logger.info("✅ Phase 14 GraphRAG test passed successfully!")


if __name__ == "__main__":
    test_graph()
