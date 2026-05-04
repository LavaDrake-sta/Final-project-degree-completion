"""
Logger Configuration - PII Detection System
Central logger for all modules. Forces UTF-8 to handle Hebrew/emoji on Windows.
"""

import logging
import sys
import io


def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger. Same name = same logger (singleton)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Force UTF-8 on Windows (avoids cp1255 UnicodeEncodeError with emoji)
    try:
        utf8_stream = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
    except AttributeError:
        utf8_stream = sys.stdout  # fallback if no .buffer (e.g. inside Streamlit)

    handler = logging.StreamHandler(utf8_stream)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


system_logger = get_logger("PII.System")

