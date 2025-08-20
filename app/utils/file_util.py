from loguru import logger
from app.database.models.file import FileModel
from app.utils.quiz_util import generate_quiz_for_file
from app.utils.topic_utils import generate_topics_for_file


def process_and_create_action_items_for_file(file_object: FileModel, user_id: str):
    logger.info(f"Processing file")
    generate_topics_for_file(
        file_content=file_object.file_content, file_id=file_object.id, user_id=user_id
    )

    logger.info(
        f"Created topics and updated knowledge map for file: {file_object.id} and user_id: {user_id}"
    )

    generate_quiz_for_file(file_id=file_object.id, user_id=user_id)

    logger.info(f"Completed quiz generation for file: {file_object.id} and user_id: {user_id}")

    return
