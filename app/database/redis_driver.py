import redis

from app.config import CELERY_BROKER_URL

redis_cursor = redis.Redis(host="localhost", port=6379, decode_responses=True)
redis_queue_cursor = redis.Redis.from_url(CELERY_BROKER_URL)
