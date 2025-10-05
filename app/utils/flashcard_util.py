from typing import List
from app.constants import ChatGptMessagePayload, ChatGptPrompts
from app.database import query_manager
from app.database.models.file import FileModel
from app.database.models.flashcard_qna import FlashCardQnAModel
from app.database.models.flashcards import FlashCardModel
from app.database.object_repository import ObjectRepository
from sqlalchemy.orm import joinedload

from app.utils.notification_util import create_notification_for_flashcard
from app.utils.g_gpt import fetch_response_from_model
from app.utils.qna_util import insert_flashcard_qna_in_db


def generate_flashcard_for_file(file_id: str, user_id: str):
    file_object: FileModel = ObjectRepository.get_object_by_id(model=FileModel, object_id=file_id)
    existing_flashcards_for_file: List[FlashCardModel] = query_manager.query_with_filter(
        model=FlashCardModel, filters=(FlashCardModel.file_id == file_id)
    )
    previous_questions: List[str] = []
    for existing_flashcard in existing_flashcards_for_file:
        qna_for_existing_flashcards: List[FlashCardQnAModel] = query_manager.query_with_filter(
            model=FlashCardQnAModel,
            filters=(FlashCardQnAModel.flashcard_id == existing_flashcard.id),
            options=[joinedload(FlashCardQnAModel.qna)],
        )
        previous_questions.extend([fqna.qna.question for fqna in qna_for_existing_flashcards])

    system_prompt_for_flashcard_agent = ChatGptPrompts.get_flashcard_generation_prompt(
        previous_questions=previous_questions
    )
    message_for_model = ChatGptMessagePayload.get_message_payload_for_pdf_questions(
        prompt=system_prompt_for_flashcard_agent,
        pdf_content=file_object.file_content,
    )
    response = fetch_response_from_model(message_for_model=message_for_model)

    flashcard: FlashCardModel = FlashCardModel(user_id=user_id, file_id=file_id)

    inserted_flashcard = ObjectRepository.insert_single_object(object_to_be_inserted=flashcard)

    total_flashcard_count = 0
    for res in response.get("questions", []):
        question: str = res.get("value")
        answer: str = res.get("answer")
        insert_flashcard_qna_in_db(
            question=question, answer=answer, flashcard_id=inserted_flashcard.id
        )
        total_flashcard_count += 1

    create_notification_for_flashcard(
        flashcard_id=flashcard.id,
        file_id=file_id,
        file_name=file_object.file_name,
        flashcard_name="",
        user_id=user_id,
    )

    return response, total_flashcard_count
