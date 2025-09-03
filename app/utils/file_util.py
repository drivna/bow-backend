from loguru import logger
from app.celery_app import celery_app
from app.database.models.file import FileModel
from app.database.object_repository import ObjectRepository
from app.utils.flashcard_util import generate_flashcard_for_file
from app.utils.quiz_util import generate_quiz_for_file
from app.utils.topic_utils import generate_topics_for_file_and_update_knowledge_map


@celery_app.task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5
)
def process_and_create_action_items_for_file_in_bg(self, file_id: str, user_id: str):
    try:
        file_object: FileModel = ObjectRepository.get_object_by_id(
            model=FileModel, object_id=file_id
        )

        logger.info(f"[{self.request.id}] Processing file: {file_id}")

        generate_topics_for_file_and_update_knowledge_map(
            file_content=file_object.file_content, file_id=file_object.id, user_id=user_id
        )

        logger.info(
            f"[{self.request.id}] Created topics and updated knowledge map for file: "
            f"{file_object.id} and user_id: {user_id}"
        )

        generate_quiz_for_file(file_id=file_object.id, user_id=user_id)

        logger.info(
            f"[{self.request.id}] Completed quiz generation for file: "
            f"{file_object.id} and user_id: {user_id}"
        )

        generate_flashcard_for_file(file_id=file_id, user_id=user_id)

        logger.info(f"{self.request.id}] Generating flashcards for file: {file_id}")
        logger.info(f"[{self.request.id}] Processed file successfully")
    except Exception as e:
        logger.warning(
            f"{self.request.id} Error processing file {file_id}, retry-{self.request.retries + 1}: {e}"
        )
        raise self.retry(exc=e, countdown=30)


def process_and_create_action_items_for_file_in_fg(file_id: str, user_id: str):
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
