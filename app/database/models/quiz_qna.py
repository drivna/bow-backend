from datetime import datetime
from typing import Any, List
from sqlalchemy import Boolean, String, ForeignKey, Enum as SqlEnum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from app.database.models.qna import QNAModel
import enum


class DifficultyLevel(enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuizQnAModel(Base):
    __tablename__ = "QUIZ_QNA"

    id: Mapped[str] = mapped_column("ID", String(100), ForeignKey("QNA.ID"), primary_key=True)

    quiz_id: Mapped[str] = mapped_column(
        "QUIZ_ID", String(100), ForeignKey("QUIZ.ID"), nullable=False, index=True
    )

    options: Mapped[str] = mapped_column("OPTIONS", Text, nullable=False)

    difficulty: Mapped[DifficultyLevel] = mapped_column(
        "DIFFICULTY", SqlEnum(DifficultyLevel), nullable=False
    )

    is_answered: Mapped[bool] = mapped_column("IS_ANSWERED", Boolean, default=False)

    is_given_to_user: Mapped[bool] = mapped_column("IS_GIVEN_TO_USER", Boolean, default=False)

    time_limit: Mapped[int] = mapped_column(
        "TIME_LIMIT", Integer, nullable=True, doc="Time allowed for this question in seconds"
    )

    # Relationships
    qna = relationship("QNAModel", back_populates="quiz_qna")
    quiz = relationship("QuizModel", back_populates="quiz_qna_items")

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        for key, value in kw.items():
            if hasattr(self, key):
                setattr(self, key, value)

        if not hasattr(self, "created_at") or self.created_at is None:
            self.created_at = current_time
        if not hasattr(self, "updated_at") or self.updated_at is None:
            self.updated_at = current_time

        if not hasattr(self, "id") or self.id is None:
            self.id = self.compute_and_get_id()

        super().__init__()

    def get_identifiers(self) -> List[Any]:
        return [self.quiz_id, self.created_at]

    def token(self) -> str:
        return "quizqna"
