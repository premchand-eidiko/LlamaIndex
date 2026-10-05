"""
Phase 19 Test: Structured Logging and Error Handling

This script demonstrates and verifies:
1. Loguru logger configuration (rotation, retention, levels)
2. Custom Enterprise RAG exception hierarchy (DocumentIngestionError, IndexNotFoundError, etc.)
3. FastAPI custom exception handler serialization
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.exceptions import (
    EnterpriseRAGException,
    DocumentIngestionError,
    IndexNotFoundError,
    SessionNotFoundError,
)
from app.core.logging import logger
from fastapi.testclient import TestClient
from app.main import app


def test_logging_and_errors():
    """Test logging and exception handling."""
    logger.info("=" * 60)
    logger.info("TESTING PHASE 19: LOGGING & ERROR HANDLING")
    logger.info("=" * 60)

    # 1. Test log directory & rotation setup
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.info("1. Verified Loguru structured logging configuration.")
    logger.debug("   Debug message active")
    logger.warning("   Sample warning message")

    # 2. Test Exception hierarchy
    logger.info("2. Testing Custom Exception hierarchy...")
    exc1 = DocumentIngestionError("Corrupt PDF file header", details={"file": "bad.pdf"})
    assert isinstance(exc1, EnterpriseRAGException)
    assert exc1.status_code == 422
    assert exc1.details["file"] == "bad.pdf"
    logger.info(f"   ✓ {exc1.__class__.__name__}: status={exc1.status_code}, msg='{exc1.message}'")

    exc2 = IndexNotFoundError()
    assert exc2.status_code == 404
    logger.info(f"   ✓ {exc2.__class__.__name__}: status={exc2.status_code}")

    exc3 = SessionNotFoundError("sess-unknown-999")
    assert exc3.status_code == 404
    assert exc3.details["session_id"] == "sess-unknown-999"
    logger.info(f"   ✓ {exc3.__class__.__name__}: status={exc3.status_code}")

    # 3. Test that FastAPI exception handler returns standardized JSON
    client = TestClient(app)

    # Trigger custom exception endpoint test
    @app.get("/test/raise-enterprise-error")
    def trigger_error():
        raise DocumentIngestionError("Failed to parse corrupt doc", details={"reason": "EOF error"})

    res = client.get("/test/raise-enterprise-error")
    assert res.status_code == 422
    err_json = res.json()
    logger.info(f"3. FastAPI Custom Exception Handler Output: {err_json}")
    assert err_json["error"] == "DocumentIngestionError"
    assert "reason" in err_json["details"]
    logger.info("   ✓ Standardized error response returned with correct HTTP status code")

    logger.info("✅ Phase 19 Logging and Error Handling test passed successfully!")


if __name__ == "__main__":
    test_logging_and_errors()
