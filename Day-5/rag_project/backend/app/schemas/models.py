"""
Pydantic Models for Request/Response Schemas

This module defines the data models used throughout the application.

Why we need Pydantic models:
- Automatic data validation
- Type safety
- Automatic JSON serialization/deserialization
- OpenAPI/Swagger documentation generation
- Clear contract for API consumers

What they do:
- Define the structure of incoming requests
- Define the structure of outgoing responses
- Validate data types and constraints
- Provide IDE autocomplete and type checking
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentMetadata(BaseModel):
    """
    Metadata model for documents.

    Why we need this:
    - Standardize metadata structure across the application
    - Validate metadata fields
    - Ensure consistent metadata for filtering and retrieval

    What it contains:
    - document_id: Unique identifier for the document
    - file_name: Original filename
    - file_type: Type of document (pdf, docx, etc.)
    - file_size: Size in bytes
    - department: Organizational department (HR, Finance, etc.)
    - document_category: Category (policy, handbook, report, etc.)
    - access_level: Access control level
    - created_at: Upload timestamp
    - version: Document version
    """

    document_id: str = Field(..., description="Unique document identifier")
    file_name: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (pdf, docx, txt, etc.)")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    department: Optional[str] = Field(None, description="Department (HR, Finance, etc.)")
    document_category: Optional[str] = Field(None, description="Document category")
    access_level: Optional[str] = Field(None, description="Access control level")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    version: Optional[str] = Field("1.0", description="Document version")


class DocumentUploadResponse(BaseModel):
    """
    Response model for document upload.

    Why we need this:
    - Provide consistent response structure
    - Include success status and metadata
    - Return document_id for reference
    """

    success: bool
    document_id: str
    file_name: str
    nodes_created: int
    message: str


class QueryRequest(BaseModel):
    """
    Request model for querying the RAG system.

    Why we need this:
    - Validate incoming query requests
    - Provide session_id for conversation context
    - Support optional metadata filters
    """

    query: str = Field(..., min_length=1, description="User query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    top_k: Optional[int] = Field(None, description="Override default top_k")


class Source(BaseModel):
    """
    Source reference model for citations.

    Why we need this:
    - Provide clear source attribution
    - Enable users to verify information
    - Support document-level tracking
    """

    file_name: str
    page: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """
    Response model for query results.

    Why we need this:
    - Provide consistent response structure
    - Include answer, sources, and metadata
    - Support streaming responses later
    """

    answer: str
    sources: List[Source]
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    """
    Message model for chat conversations.

    Why we need this:
    - Structure chat messages
    - Support role differentiation (user/assistant)
    - Enable conversation history tracking
    """

    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.

    Why we need this:
    - Support conversational interactions
    - Maintain session context
    - Accept user messages
    """

    message: str = Field(..., min_length=1, description="User message")
    session_id: str = Field(..., description="Session ID for conversation context")


class ChatResponse(BaseModel):
    """
    Response model for chat endpoint.

    Why we need this:
    - Provide assistant response
    - Include conversation history
    - Provide source citations
    """

    response: str
    sources: List[Source]
    session_id: str
    conversation_history: List[ChatMessage]


class HealthResponse(BaseModel):
    """
    Response model for health check.

    Why we need this:
    - Simple health check response
    - Include service status
    """

    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    index_loaded: bool = False
    documents_count: int = 0


class HybridQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query string")
    top_k: Optional[int] = Field(5, description="Number of nodes to retrieve")
    alpha: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Weight: 1.0=vector, 0.0=keyword")


class GraphExploreRequest(BaseModel):
    entity: str = Field(..., min_length=1, description="Starting entity for graph traversal")
    max_depth: Optional[int] = Field(2, ge=1, le=5, description="BFS depth for traversal")


class GraphExploreResponse(BaseModel):
    entity: str
    paths_found: int
    network_subgraph: List[str]

