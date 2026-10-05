"""
Logging Configuration Module

This module sets up structured logging for the Enterprise RAG Assistant.

Why we need structured logging:
- Track document ingestion and processing
- Monitor query performance and retrieval metrics
- Debug issues in production
- Audit access and operations
- Meet enterprise compliance requirements

What it does:
- Configures Loguru logger with appropriate formatting
- Sets up file rotation to manage log file sizes
- Configures different log levels for different environments
- Provides a consistent logging interface across all modules
"""

import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """
    Configure the logging system for the application.

    Why we need this function:
    - Centralize logging configuration
    - Ensure consistent logging format across the application
    - Set up log file rotation to prevent disk space issues
    - Configure appropriate log levels based on environment

    What it does:
    1. Removes the default handler to avoid duplicate logs
    2. Adds a console handler with colored output for development
    3. Adds a file handler with rotation for persistent logs
    4. Sets the log level based on configuration

    What would happen if we removed it:
    - Logs would only go to console and not be persisted
    - No log rotation could cause disk space issues
    - Inconsistent log formatting across modules
    - Hard to debug production issues
    """

    # Remove default handler
    logger.remove()

    # Add console handler with colored output
    # This shows logs in the terminal during development
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )

    # Add file handler with rotation
    # This persists logs to disk and rotates them when they get too large
    logger.add(
        "logs/app.log",
        rotation="500 MB",  # Rotate when file reaches 500 MB
        retention="10 days",  # Keep logs for 10 days
        compression="zip",  # Compress rotated logs
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level
    )

    # Add separate error log file
    # This makes it easier to find and debug errors
    logger.add(
        "logs/error.log",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR"
    )

    return logger


# Initialize logging when module is imported
setup_logging()
