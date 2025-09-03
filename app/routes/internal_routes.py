import json
from flask_restx import Namespace, Resource
from flask import jsonify
import redis
from app import celery_app
from app.database.redis_driver import redis_queue_cursor

internal_api_ns = Namespace("Internal", description="APIs for internal queue analytics")


@internal_api_ns.route("/dashboard")
class FileParsingRoutes(Resource):
    def get():
        queue_name = celery_app.conf.task_default_queue
        pending_count = redis_queue_cursor.llen(queue_name)

        insp = celery_app.control.inspect()
        active = insp.active() or {}
        reserved = insp.reserved() or {}
        scheduled = insp.scheduled() or {}

        meta_keys = redis_queue_cursor.keys("celery-task-meta-*")
        last_10 = []
        for key in meta_keys[-10:]:
            data = json.loads(redis_queue_cursor.get(key))
            last_10.append(
                {
                    "task_id": data.get("task_id"),
                    "status": data.get("status"),
                    "result": data.get("result"),
                    "date_done": data.get("date_done"),
                }
            )

        return jsonify(
            {
                "queue_name": queue_name,
                "pending": pending_count,
                "active": active,
                "reserved": reserved,
                "scheduled": scheduled,
                "recent_results": last_10,
            }
        )
