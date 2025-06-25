import logging
import sys
import os

LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"

# Set up a single logger for the whole app
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    stream=sys.stdout
)

def get_logger(name=None):
    return logging.getLogger(name or "app")

def set_log_level(level):
    """Set the logging level for all loggers"""
    logging.getLogger().setLevel(level)
    # Also set for specific loggers
    for logger_name in ["ingest_worker", "youtube_strategy", "api.ingest", "api.temporal"]:
        logging.getLogger(logger_name).setLevel(level)

def enable_debug_logging():
    """Enable debug logging for detailed background task monitoring"""
    set_log_level(logging.DEBUG)
    print("[LOGGING] Debug logging enabled - you'll see detailed background task logs")

def enable_info_logging():
    """Enable info logging for general background task monitoring"""
    set_log_level(logging.INFO)
    print("[LOGGING] Info logging enabled - you'll see general background task progress") 