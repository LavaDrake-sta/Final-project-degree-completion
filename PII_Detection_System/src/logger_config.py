"""
Logger Configuration - PII Detection System
Central logger for all modules. Forces UTF-8 to handle Hebrew/emoji on Windows.
"""

import logging
import sys
import io
import time
from functools import wraps


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


def trace_execution(func):
    """
    Decorator that logs the entry and exit of a function, 
    along with its execution time.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        system_logger.info(f"▶ Starting execution: {func.__name__}")
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            system_logger.info(f"✔ Finished execution: {func.__name__} (took {execution_time:.2f} seconds)")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            system_logger.error(f"❌ Error executing {func.__name__} (after {execution_time:.2f} seconds): {e}")
            raise
    return wrapper


def log_progress(current: int, total: int, task_name: str, length: int = 20):
    """
    Logs a progress bar in the terminal.
    Example: [14:30:01] ⏳ התקדמות סריקת PDF: [████████--] 80% (4 מתוך 5)
    """
    if total == 0:
        return
        
    percent = current / total
    filled = int(length * percent)
    bar = '█' * filled + '-' * (length - filled)
    
    msg = f"⏳ Progress {task_name}: [{bar}] {int(percent * 100)}% ({current}/{total})"
    # We use INFO level to make sure it prints
    system_logger.info(msg)

