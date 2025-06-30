from datetime import datetime
from typing import Any, List
from sqlalchemy import String, ForeignKey, Boolean, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class QuizUserAnswersModel(Base):
    __tablename__ = "QUIZ_USER_ANSWERS"

    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(
        "USER_ID", String(255), ForeignKey("USERS.ID"), nullable=False, index=True
    )

    quiz_id: Mapped[str] = mapped_column(
        "QUIZ_ID", String(100), ForeignKey("QUIZ.ID"), nullable=False, index=True
    )

    qna_id: Mapped[str] = mapped_column(
        "QNA_ID", String(100), ForeignKey("QNA.ID"), nullable=False, index=True
    )

    user_answer: Mapped[str] = mapped_column("USER_ANSWER", Text, nullable=False)

    is_correct: Mapped[bool] = mapped_column("IS_CORRECT", Boolean, nullable=False)

    time_taken: Mapped[int] = mapped_column(
        "TIME_TAKEN", Integer, nullable=True, doc="Time taken to answer in seconds"
    )

    # Relationships
    quiz = relationship("QuizModel")
    qna = relationship("QNAModel")

    def __init__(self, **kw: Any):
        current_time = datetime.now()
        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}
        kwargs.setdefault("created_at", current_time)
        kwargs.setdefault("updated_at", current_time)
        kwargs.setdefault("id", self.compute_and_get_id())
        super().__init__(**kwargs)

    def token(self) -> str:
        return "quizuseranswers"

    def get_identifiers(self) -> List[Any]:
        return [self.user_id, self.quiz_id, self.qna_id, self.created_at]
