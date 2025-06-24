import logging
import sys

LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"

# Set up a single logger for the whole app
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    stream=sys.stdout
)

def get_logger(name=None):
    return logging.getLogger(name or "app") 