from app.database.models.qna import QNAModel, QuestionSource
from app.database.object_repository import ObjectRepository


def insert_question_and_answer_in_db(
    question: str, answer: str, source: QuestionSource, source_id: str
) -> None:
    qna: QNAModel = QNAModel(source=source, source_id=source_id, question=question, answer=answer)
    return ObjectRepository.insert_single_object(qna)
