import redis

redis_cursor = redis.Redis(host="localhost", port=6379, decode_responses=True)
