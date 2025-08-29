import json
import time
import uuid
from app.database.redis_driver import redis_cursor


def enqueue_job(task_type, payload):
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "task_type": task_type,
        "payload": payload,
        "retry_count": 0,
        "status": "queued",
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    redis_cursor.hset(f"job:{job_id}", mapping=job)

    redis_cursor.rpush("jobs", json.dumps(job))

    return job_id


def update_job_status(job_id, status, retry_count=0):
    redis_cursor.hset(
        f"job:{job_id}",
        mapping={"status": status, "retry_count": retry_count, "updated_at": time.time()},
    )
