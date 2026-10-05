"""
Enterprise Exceptions Module (Phase 19)

Custom domain-specific exceptions for the Enterprise RAG Assistant.
"""

from typing import Optional, Dict, Any


class EnterpriseRAGException(Exception):
    """Base exception for all Enterprise RAG errors."""

    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DocumentIngestionError(EnterpriseRAGException):
    """Raised when parsing, loading, or chunking a document fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, details=details)


class IndexNotFoundError(EnterpriseRAGException):
    """Raised when an operation requires an initialized index but none exists."""

    def __init__(self, message: str = "No document index is currently initialized.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=404, details=details)


class RetrievalError(EnterpriseRAGException):
    """Raised when retrieval operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=500, details=details)


class SessionNotFoundError(EnterpriseRAGException):
    """Raised when a chat session ID does not exist."""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session with ID '{session_id}' was not found.",
            status_code=404,
            details={"session_id": session_id},
        )
