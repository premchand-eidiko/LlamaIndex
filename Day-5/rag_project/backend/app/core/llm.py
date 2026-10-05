"""
Core LLM Configuration Module

Provides a centralized factory for LLMs with full Groq and OpenAI support.
If GROQ_API_KEY is configured in .env, Groq is prioritized for ultra-fast inference.
"""

from typing import Optional
from llama_index.core.llms import LLM
from llama_index.core import Settings
from loguru import logger

from app.core.config import settings


def get_llm() -> Optional[LLM]:
    """
    Get configured LLM. Supports Groq (priority if groq_api_key provided) and OpenAI.
    """
    # 1. Groq LLM (High-speed enterprise inference)
    if settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here":
        try:
            from llama_index.llms.groq import Groq
            from groq import Groq as GroqClient

            # Verify which models are accessible to this API key
            target_model = settings.groq_model
            candidate_models = [target_model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "llama-3.3-70b-versatile"]

            chosen_model = None
            try:
                gc = GroqClient(api_key=settings.groq_api_key)
                active_models = {m.id for m in gc.models.list().data}
                for candidate in candidate_models:
                    if candidate in active_models:
                        chosen_model = candidate
                        break
            except Exception as e:
                logger.debug(f"Groq model list check: {e}")

            if not chosen_model:
                chosen_model = target_model

            llm = Groq(
                model=chosen_model,
                api_key=settings.groq_api_key,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            Settings.llm = llm
            logger.info(f"Initialized Groq LLM: {chosen_model}")
            return llm

        except Exception as e:
            logger.error(f"Failed to initialize Groq LLM: {e}")

    # 2. OpenAI LLM (Fallback)
    if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
        try:
            from llama_index.llms.openai import OpenAI
            llm = OpenAI(
                model=settings.llm_model,
                api_key=settings.openai_api_key,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            Settings.llm = llm
            logger.info(f"Initialized OpenAI LLM: {settings.llm_model}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {e}")

    logger.warning("No active LLM API key configured (neither GROQ_API_KEY nor OPENAI_API_KEY). Running in mock mode.")
    return None
