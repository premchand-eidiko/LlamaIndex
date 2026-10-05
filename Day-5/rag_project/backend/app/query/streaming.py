"""
Streaming Module (Phase 16)

This module implements token-by-token streaming response generation
for query engines and chat engines.

Why we need Streaming:
- LLM response generation can take 5-10 seconds for detailed corporate syntheses.
- Streaming provides immediate feedback (Time-To-First-Token < 500ms).
- Compatible with FastAPI StreamingResponse and Server-Sent Events (SSE).
"""

from typing import AsyncGenerator, Generator, Optional, Any, Dict
import asyncio
from llama_index.core import VectorStoreIndex
from llama_index.core.base.response.schema import StreamingResponse as LlamaStreamingResponse
from loguru import logger

from app.core.config import settings


class StreamingManager:
    """
    Manager for creating streaming query engines and yielding streaming tokens.
    """

    def __init__(self):
        logger.info("Initialized StreamingManager")

    def create_streaming_query_engine(
        self,
        index: VectorStoreIndex,
        similarity_top_k: Optional[int] = None,
    ):
        """Create a query engine configured for streaming output."""
        k = similarity_top_k or settings.similarity_top_k
        logger.info(f"Creating streaming query engine (similarity_top_k={k})")
        return index.as_query_engine(
            similarity_top_k=k,
            streaming=True,
        )

    def stream_tokens(self, streaming_response: Any) -> Generator[str, None, None]:
        """Yield tokens from a LlamaIndex StreamingResponse."""
        if hasattr(streaming_response, "response_gen"):
            for token in streaming_response.response_gen:
                yield token
        elif hasattr(streaming_response, "__iter__"):
            for chunk in streaming_response:
                yield str(chunk)
        else:
            yield str(streaming_response)

    async def async_stream_tokens(self, full_text: str, delay: float = 0.02) -> AsyncGenerator[str, None]:
        """Simulate or stream tokens asynchronously for SSE / FastAPI."""
        words = full_text.split(" ")
        for word in words:
            yield word + " "
            await asyncio.sleep(delay)


# Global singleton
streaming_manager = StreamingManager()
