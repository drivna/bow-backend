from typing import Any, Dict

from app.database.models.activity import ActivityModel
from app.database.object_repository import ObjectRepository


def create_or_update_activity_for_user(
    user_id: str, activity_description: Dict[str, Any], activity_item_id: str, activity_type: str
):
    activity: ActivityModel = ActivityModel(
        user_id=user_id,
        activity_description=activity_description,
        activity_item_id=activity_item_id,
        activity_type=activity_type,
    )
    activity_exists = None
    try:
        activity_exists = ObjectRepository.get_object_by_id(
            model=ActivityModel, object_id=activity.id
        )
    except Exception:
        pass

    if not activity_exists:
        ObjectRepository.insert_single_object(object_to_be_inserted=activity)
        return
    if activity_type != "FLASHCARD":
        activity_exists.activity_description = activity_description
        ObjectRepository.update_single_object(activity_description)
        return

    existing_flashcards_count = activity_exists.activity_description.get("flashcard_count", 0)
    current_flashcards_count = activity_description.get("flashcard_count", 0)
    updated_description = get_description_for_flashcard_activity(
        flashcard_count=existing_flashcards_count + current_flashcards_count,
        file_id=activity_description.get("file_id"),
        file_name=activity_description.get("file_name"),
    )

    activity_exists.activity_description = updated_description
    ObjectRepository.update_single_object(activity_exists)
    return


def create_activity_for_file_read(file_id: str, file_name: str, user_id: str):
    description: Dict[str, Any] = {"file_name": file_name}
    create_or_update_activity_for_user(
        user_id=user_id,
        activity_description=description,
        activity_item_id=file_id,
        activity_type="FILE_READ",
    )


def create_activity_for_quiz(
    quiz_id: str, quiz_summary: Dict[str, Any], quiz_name: str, user_id: str
) -> None:
    description: Dict[str, Any] = {
        "quiz_id": quiz_id,
        "quiz_summary": quiz_summary,
        "quiz_name": quiz_name,
    }

    create_or_update_activity_for_user(
        user_id=user_id,
        activity_description=description,
        activity_item_id=quiz_id,
        activity_type="QUIZ",
    )


def get_description_for_flashcard_activity(flashcard_count, file_id, file_name) -> Dict[str, Any]:
    return {"flashcard_count": flashcard_count, "file_id": file_id, "file_name": file_name}


def create_activity_for_flashcard(
    file_id: str, file_name: str, flashcards_count: str, user_id: str
) -> None:
    description: Dict[str, Any] = get_description_for_flashcard_activity(
        flashcard_count=flashcards_count, file_name=file_name, file_id=file_id
    )
    create_or_update_activity_for_user(
        user_id=user_id,
        activity_description=description,
        activity_item_id=file_id,
        activity_type="FLASHCARD",
    )
