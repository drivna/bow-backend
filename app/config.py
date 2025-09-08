import os
from dotenv import load_dotenv
load_dotenv()

CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
OPEN_AI_API_KEY: str = os.getenv("CHAT_GPT_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("CELERY_BROKER_URL", "")
CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CUSTOM_USER_ID: str = "user_17ae337cff"
APP_PORT: int = os.getenv("APP_PORT", "4000")