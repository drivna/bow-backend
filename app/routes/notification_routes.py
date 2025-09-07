from typing import Any, Dict, List
from flask import request
from flask_restx import Resource, Namespace
from flask_restx.reqparse import RequestParser, ParseResult

from app.config import CUSTOM_USER_ID
from app.database import query_manager
from app.database.models.noitifications import NotificationModel
from app.middleware.auth import authenticate_user

notification_api_ns = Namespace("notification", description="Notification APIs")


@notification_api_ns.route("")
class NotificationRoutes(Resource):
    notification_parser: RequestParser = RequestParser()
    notification_parser.add_argument(
        "page", type=int, help="Page number for pagination", required=False, default=1
    )
    notification_parser.add_argument(
        "per_page", type=int, help="Number of notifications per page", required=False, default=10
    )

    @notification_api_ns.expect(notification_parser)
    @authenticate_user
    def get(self):
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID

        args = self.notification_parser.parse_args()
        page = args.get("page", 1)
        per_page = args.get("per_page", 10)

        offset = (page - 1) * per_page

        notifications: List[NotificationModel] = query_manager.query_with_filter(
            model=NotificationModel,
            filters=(NotificationModel.user_id == user_id),
            order_by=NotificationModel.updated_at.desc(),
            offset=offset,
            limit=per_page,
        )

        total_notifications_count: int = query_manager.query_count_with_filter(
            model=NotificationModel,
            filters=(NotificationModel.user_id == user_id),
        )
        has_next: bool = page * per_page < total_notifications_count

        response: List[Dict[str, Any]] = []
        for notif in notifications:
            res = {
                "id": notif.id,
                "description": notif.description,
                "message": notif.message,
                "is_relayed": notif.is_relayed,
                "created_at": notif.created_at.isoformat(),
                "updated_at": notif.updated_at.isoformat(),
            }
            response.append(res)

        return {
            "error": None,
            "message": "Notifications fetched successfully",
            "data": {
                "notifications": response,
                "has_next": has_next,
                "totalCount": total_notifications_count,
            },
        }, 200
