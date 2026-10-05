"""
Simple test to verify the RAG system works.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings

print("=" * 60)
print("ENTERPRISE RAG ASSISTANT - SIMPLE TEST")
print("=" * 60)

print(f"\nConfiguration:")
print(f"  LLM Model: {settings.llm_model}")
print(f"  Embedding Model: {settings.embedding_model}")
print(f"  Storage Dir: {settings.storage_dir}")
print(f"  Documents Dir: {settings.documents_dir}")
print(f"  API Host: {settings.api_host}")
print(f"  API Port: {settings.api_port}")

print(f"\nAPI Key Configured: {bool(settings.openai_api_key and settings.openai_api_key != 'your_openai_api_key_here')}")

if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
    print("\n⚠️  WARNING: OPENAI_API_KEY not configured")
    print("To use the system:")
    print("1. Copy .env.example to .env")
    print("2. Add your OpenAI API key to .env")
    print("3. Run: python -m app.main")
else:
    print("\n✅ Ready to start!")
    print("Run: python -m app.main")

print("\nAPI Documentation will be available at:")
print(f"  http://{settings.api_host}:{settings.api_port}/docs")
print("=" * 60)
