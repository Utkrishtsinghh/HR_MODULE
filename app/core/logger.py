import logging

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("utk")

from app.core.logger import logger

logger.info("Resume uploaded")
logger.info("User logged in")
logger.error("Email failed")