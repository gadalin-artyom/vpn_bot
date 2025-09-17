from loguru import logger
import sys
import constants

logger.remove()
logger.add(
    sys.stderr,
    format=constants.LOG_FORMAT,
    level="INFO"
)

def get_logger(name: str):
    return logger.bind(name=name)