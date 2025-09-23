from loguru import logger

from kimi_cli.share import get_share_dir

logger.remove()
logger.add(get_share_dir() / "logs" / "kimi.log", rotation="06:00", retention="10 days")
