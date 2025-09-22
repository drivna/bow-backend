import redis

from app.config import CELERY_BROKER_URL, REDIS_DB, REDIS_HOST

redis_cursor = redis.Redis(host=REDIS_HOST, port=6379, db=REDIS_DB, decode_responses=True)
redis_queue_cursor = redis.Redis.from_url(CELERY_BROKER_URL)
