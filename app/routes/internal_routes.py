from typing import Any, Dict, List
from flask_restx import Namespace, Resource
from flask import request
from app.database.redis_driver import redis_cursor

internal_api_ns = Namespace("Internal", description="APIs for internal queue analytics")


@internal_api_ns.route("/jobs/analytics")
class JobsAnalyticsRoutes(Resource):
    def get(self):
        try:
            user_id = request.user_id
        except Exception:
            user_id = "user_17ae337cff"

        try:
            job_keys = redis_cursor.keys("job:*")
            jobs = [
                redis_cursor.hgetall(k)
                for k in job_keys
                if redis_cursor.hgetall(k).get("user_id") == user_id
            ]

            status_counts: Dict[str, int] = {}
            for job in jobs:
                status = job.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            # Format response
            jobs_response: List[Dict[str, Any]] = []
            for job in jobs:
                job_res = {
                    "id": job.get("id"),
                    "task_type": job.get("task_type"),
                    "status": job.get("status"),
                    "retry_count": int(job.get("retry_count", 0)),
                    "created_at": job.get("created_at"),
                    "updated_at": job.get("updated_at"),
                }
                jobs_response.append(job_res)

            response = {
                "total_jobs": len(jobs),
                "status_counts": status_counts,
                "jobs": jobs_response,
            }

            return {
                "error": None,
                "message": "Job analytics fetched successfully",
                "data": response,
            }, 200

        except Exception as e:
            return {
                "error": str(e),
                "message": "Failed to fetch job analytics",
                "data": None,
            }, 500
