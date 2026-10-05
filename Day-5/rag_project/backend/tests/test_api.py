"""
Phase 17 Test: FastAPI Modular API Endpoints

This script demonstrates and verifies:
1. Health check endpoint (/health)
2. Document listing endpoint (/api/v1/documents)
3. Conversational chat endpoint (/api/v1/chat)
4. Knowledge Graph exploration endpoint (/api/v1/graph/explore)
5. Root documentation redirection (/)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.core.logging import logger


def test_fastapi_endpoints():
    """Test all primary modular API routes."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 17: FASTAPI MODULAR APPLICATION")
    logger.info("=" * 60)

    client = TestClient(app)

    # 1. Test Root
    res_root = client.get("/")
    assert res_root.status_code == 200
    data = res_root.json()
    logger.info(f"1. Root endpoint: {data['message']} (Docs: {data['docs_url']})")

    # 2. Test Health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    logger.info(f"2. Health endpoint: {res_health.json()}")

    # 3. Test Documents list
    res_docs = client.get("/api/v1/documents")
    assert res_docs.status_code == 200
    logger.info(f"3. Documents endpoint: Found {res_docs.json()['count']} documents")

    # 4. Test Chat endpoint
    chat_payload = {
        "message": "What is the policy for bereavement leave?",
        "session_id": "test-session-api-1",
    }
    res_chat = client.post("/api/v1/chat", json=chat_payload)
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    logger.info(f"4. Chat endpoint: Response received for session {chat_data['session_id']}")
    logger.info(f"   Reply: {chat_data['response'][:60]}...")

    # 5. Test Graph Explore endpoint
    graph_payload = {"entity": "HR Department", "max_depth": 2}
    res_graph = client.post("/api/v1/graph/explore", json=graph_payload)
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    logger.info(f"5. Graph Explore endpoint: Entity='{graph_data['entity']}', paths={graph_data['paths_found']}")

    logger.info("✅ Phase 17 FastAPI Modular API test passed successfully!")


if __name__ == "__main__":
    test_fastapi_endpoints()
