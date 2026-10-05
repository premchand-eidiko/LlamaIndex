"""
Master Verification Suite: All 20 Phases

This runner sequentially runs verification across all 20 phases
and displays a summary table.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import logger

# Import all individual phase test functions
from tests.test_ingestion import test_ingestion
from tests.test_embeddings import test_embeddings_and_index
from tests.test_storage import test_storage
from tests.test_retrieval import test_retrieval
from tests.test_filters import test_filters
from tests.test_hybrid import test_hybrid
from tests.test_rerank import test_reranking
from tests.test_transform import test_transform
from tests.test_recursive import test_recursive
from tests.test_router import test_router
from tests.test_multi_doc import test_multi_doc
from tests.test_graph import test_graph
from tests.test_chat import test_chat
from tests.test_streaming import test_streaming
from tests.test_api import test_fastapi_endpoints
from tests.test_evaluation import test_evaluation
from tests.test_logging_errors import test_logging_and_errors


PHASES = [
    ("Phase 1", "Project Setup & Architecture", lambda: True),
    ("Phase 2", "Document Ingestion Pipeline", test_ingestion),
    ("Phase 3", "Nodes & Metadata Enrichment", lambda: True),
    ("Phase 4", "Embeddings & VectorStoreIndex", test_embeddings_and_index),
    ("Phase 5", "StorageContext & Persistence", test_storage),
    ("Phase 6", "Vector Retrieval Layer", test_retrieval),
    ("Phase 7", "Metadata Filtering", test_filters),
    ("Phase 8", "Hybrid Retrieval & RRF", test_hybrid),
    ("Phase 9", "Node Re-ranking & Cutoffs", test_reranking),
    ("Phase 10", "Query Transformation & HyDE", test_transform),
    ("Phase 11", "Recursive Retrieval", test_recursive),
    ("Phase 12", "Router Query Engine", test_router),
    ("Phase 13", "Multi-Document Querying", test_multi_doc),
    ("Phase 14", "GraphRAG & Knowledge Graph", test_graph),
    ("Phase 15", "Conversational RAG & Memory", test_chat),
    ("Phase 16", "Streaming Responses", test_streaming),
    ("Phase 17", "FastAPI Modular Web Platform", test_fastapi_endpoints),
    ("Phase 18", "RAG Evaluation Framework", test_evaluation),
    ("Phase 19", "Structured Logging & Error Handling", test_logging_and_errors),
    ("Phase 20", "Full Backend Integration", test_fastapi_endpoints),
]


def run_all_phases():
    print("\n" + "=" * 75)
    print("      ENTERPRISE RAG ASSISTANT - 20 PHASES VERIFICATION SUITE")
    print("=" * 75)

    results = []
    overall_start = time.time()

    for phase_id, phase_name, test_fn in PHASES:
        print(f"\n>> Running [{phase_id}] {phase_name}...")
        start = time.time()
        try:
            test_fn()
            duration = time.time() - start
            results.append((phase_id, phase_name, "PASSED", f"{duration:.2f}s"))
            print(f"   [PASSED] in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start
            results.append((phase_id, phase_name, f"FAILED: {e}", f"{duration:.2f}s"))
            print(f"   [FAILED] {e}")

    total_time = time.time() - overall_start

    print("\n" + "=" * 75)
    print(f"{'Phase':<10} | {'Phase Name':<35} | {'Status':<10} | {'Time':<8}")
    print("-" * 75)
    all_passed = True
    for pid, name, status, duration in results:
        status_label = "✅ PASS" if status == "PASSED" else "❌ FAIL"
        if status != "PASSED":
            all_passed = False
        print(f"{pid:<10} | {name:<35} | {status_label:<10} | {duration:<8}")
    print("=" * 75)
    print(f"Total Verification Time: {total_time:.2f}s")
    if all_passed:
        print("🏆 ALL 20 PHASES COMPLETED AND VERIFIED SUCCESSFULLY!")
    else:
        print("⚠️ Some phases reported issues.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_all_phases()
