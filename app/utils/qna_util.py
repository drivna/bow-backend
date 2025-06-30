from app.database.models.qna import QNAModel
from app.database.models.flashcard_qna import FlashCardQnAModel
from app.database.object_repository import ObjectRepository
from datetime import datetime


def insert_flashcard_qna_in_db(question: str, answer: str, flashcard_id: str) -> None:
    # Step 1: Create QNA
    qna = QNAModel(question=question, answer=answer)
    ObjectRepository.insert_single_object(qna)

    # Step 2: Link QNA to Flashcard
    flashcard_qna = FlashCardQnAModel(flashcard_id=flashcard_id, id=qna.id)
    ObjectRepository.insert_single_object(flashcard_qna)

    return qna
