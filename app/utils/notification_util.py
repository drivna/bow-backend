from typing import Any, Dict, Tuple

from loguru import logger
from app.celery_app import celery_app
from app.database.models.noitifications import NotificationModel
from app.database.object_repository import ObjectRepository
from app.utils.ws_util import send_to_room


def build_notification_description(
    type: str, file_id: str, name: str, object_id: str, file_name: str
) -> Dict[str, str]:
    """
    Build a structured description dict for notifications.

    Args:
        type (str): Type of notification ("quiz" or "flashcard").
        file_id (str): ID of the associated file.
        name (str): Quiz/Flashcard name.
        object_id (str): Quiz ID or Flashcard ID.

    Returns:
        Dict[str, str]: Structured description.
    """
    if type == "quiz":
        return {
            "file_id": file_id,
            "quiz_name": name,
            "quiz_id": object_id,
            "file_name": file_name,
            "message": "Quiz generated",
        }
    elif type == "flashcard":
        return {
            "file_id": file_id,
            "flashcard_name": name,
            "flashcard_id": object_id,
            "file_name": file_name,
            "message": "Flashcard generated",
        }
    else:
        raise ValueError(f"Unsupported notification type: {type}")


def create_notification_for_quiz(
    quiz_id: str, file_id: str, file_name: str, quiz_name: str, user_id: str
) -> None:
    description: Dict[str, str] = build_notification_description(
        type="quiz", file_id=file_id, name=quiz_name, object_id=quiz_id, file_name=file_name
    )
    create_notification(user_id=user_id, description=description, message="Quiz Generated")


def create_notification_for_flashcard(
    flashcard_id: str, file_id: str, file_name: str, flashcard_name: str, user_id: str
) -> None:
    description: Dict[str, str] = build_notification_description(
        type="flashcard",
        file_id=file_id,
        name=flashcard_name,
        object_id=flashcard_id,
        file_name=file_name,
    )
    create_notification(user_id=user_id, description=description, message="Flashcard Generated")

    schedule_notification(user_id=user_id, description=description)


def create_notification(user_id: str, description: str, message: str):
    """
    Create and insert a new notification for a given user.

    Args:
        user_id (str): ID of the user who will receive the notification.
        description (str): Short description of the notification.
        message (str): Detailed message content.
        is_relayed (bool, optional): Whether the notification has already been relayed. Defaults to False.

    Returns:
        Tuple[NotificationModel, bool]: The inserted notification object and success flag.
    """
    notification = NotificationModel(
        user_id=user_id, description=description, message=message, is_relayed=False
    )

    inserted_notification = ObjectRepository.insert_single_object(
        object_to_be_inserted=notification
    )

    return inserted_notification


def schedule_notification(user_id: str, description: Dict[str, Any], delay_seconds: int = 600):
    notify_user.apply_async(
        kwargs={"user_id": user_id, "description": description}, countdown=delay_seconds
    )


@celery_app.task(bind=True)
def notify_user(self, user_id: str, description: Dict[str, Any]):
    logger.info(f"Notifying user: {user_id}, description: {description}")
    send_to_room(user_id=user_id, message=description, message_type="message", key="notification")
    return
