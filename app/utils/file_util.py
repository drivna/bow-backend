from loguru import logger
from app.database.models.file import FileModel
from app.database.object_repository import ObjectRepository
from app.utils.flashcard_util import generate_flashcard_for_file
from app.utils.quiz_util import generate_quiz_for_file
from app.utils.topic_utils import generate_topics_for_file_and_update_knowledge_map


def process_and_create_action_items_for_file(file_id: str, user_id: str):
    file_object: FileModel = ObjectRepository.get_object_by_id(model=FileModel, object_id=file_id)
    logger.info(f"Processing file: {file_id}")
    generate_topics_for_file_and_update_knowledge_map(
        file_content=file_object.file_content, file_id=file_object.id, user_id=user_id
    )

    logger.info(
        f"Created topics and updated knowledge map for file: {file_object.id} and user_id: {user_id}"
    )

    generate_quiz_for_file(file_id=file_object.id, user_id=user_id)

    logger.info(f"Completed quiz generation for file: {file_object.id} and user_id: {user_id}")

    generate_flashcard_for_file(file_id=file_id, user_id=user_id)

    logger.info(f"Generating flashcards for file: {file_id}")

    return
