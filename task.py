import json

from loguru import logger
from app.database.redis_driver import redis_cursor
from app.queue.redis_queue import update_job_status
from app.task_constants import TASK_HANDLERS


def worker_loop():
    worker_id: int = 1
    while True:
        logger.info(f"Running worker loop, worker_id: {worker_id}")
        try:
            _, job_data = redis_cursor.lpop("jobs")
            job = json.loads(job_data)

            job_id = job["id"]
            task_type = job["task_type"]

            update_job_status(job_id, "running", job["retry_count"])

            try:
                handler = TASK_HANDLERS.get(task_type)
                if not handler:
                    raise ValueError(f"No handler for task_type={task_type}")

                handler(**job["payload"])

                update_job_status(job_id, "success", job["retry_count"])
                print(f"Worker {worker_id}>> Success: {task_type} ({job_id})")

            except Exception as e:
                retries = job["retry_count"] + 1
                if retries < 5:
                    job["retry_count"] = retries
                    update_job_status(job_id, "retrying", retries)
                    redis_cursor.rpush("jobs", json.dumps(job))
                else:
                    update_job_status(job_id, "failed", retries)
                    print(f"Worker {worker_id}>> Failed permanently: {task_type} ({job_id}) -> {e}")
            worker_id += 1
        except Exception as e:
            print(e)


from task import worker_loop

if __name__ == "__main__":
    worker_loop()
