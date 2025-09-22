import os
from dotenv import load_dotenv
from loguru import logger
load_dotenv()

CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
OPEN_AI_API_KEY: str = os.getenv("CHAT_GPT_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("CELERY_BROKER_URL", "")
CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CUSTOM_USER_ID: str = "user_17ae337cff"
APP_PORT: int = os.getenv("APP_PORT", "4000")
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_DB: str = os.getenv("REDIS_DB", "3")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

logger.info("Inside config file")
logger.info(f"Celery broker url: {CELERY_BROKER_URL}")
logger.info(f"OPEN_AI_API_KEY: {OPEN_AI_API_KEY}")
logger.info(f"GEMINI_API_KEY: {GEMINI_API_KEY}")
logger.info(f"CELERY_RESULT_BACKEND: {CELERY_RESULT_BACKEND}")
logger.info(f"CUSTOM_USER_ID: {CUSTOM_USER_ID}")
logger.info(f"APP_PORT: {APP_PORT}")
logger.info(f"REDIS_HOST: {REDIS_HOST}")
logger.info(f"REDIS_DB: {REDIS_DB}")
logger.info("Exiting config file")
