from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from sqlalchemy import JSON, Boolean, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class QuizModel(Base):
    __tablename__ = "QUIZ"

    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(
        "USER_ID", String(255), ForeignKey("USERS.ID"), nullable=False, index=True
    )

    file_id: Mapped[str] = mapped_column(
        "FILE_ID", String(255), ForeignKey("FILES.ID"), nullable=False, index=True
    )
    quiz_name: Mapped[str] = mapped_column(
        "QUIZ_NAME",
        String(255),
        nullable=False,
    )
    quiz_summary: Mapped[Dict[str, Any]] = mapped_column("SUMMARY", JSON, default=dict)

    has_started: Mapped[bool] = mapped_column("HAS_STARTED", Boolean, nullable=False, default=False)
    has_completed: Mapped[bool] = mapped_column(
        "HAS_COMPLETED", Boolean, nullable=False, default=False
    )

    # Relationship to QuizQnAModel
    quiz_qna_items = relationship("QuizQnAModel", back_populates="quiz")

    def __init__(self, **kw: Any):
        current_time = datetime.now()
        for key, value in kw.items():
            if key in self.__dir__():
                setattr(self, key, value)

        if not hasattr(self, "created_at") or self.created_at is None:
            self.created_at = current_time
        if not hasattr(self, "updated_at") or self.updated_at is None:
            self.updated_at = current_time

        if not hasattr(self, "id") or self.id is None:
            self.id = self.compute_and_get_id()

        super().__init__()

    def token(self) -> str:
        return "quiz"

    def get_identifiers(self) -> List[Any]:
        print([self.user_id, self.file_id, self.created_at, self.quiz_name])
        return [self.user_id, self.file_id, self.created_at, self.quiz_name]

    def to_dict(self) -> Dict[str, Any]:
        quiz_summary = self.quiz_summary or {}
        quiz_summary["totalQuestions"] = 10
        return {
            "id": self.id,
            "user_id": self.user_id,
            "file_id": self.file_id,
            "quiz_name": self.quiz_name,
            "quiz_summary": quiz_summary,
            "created_at": self.created_at.isoformat()
            if hasattr(self, "created_at") and self.created_at
            else None,
            "updated_at": self.updated_at.isoformat()
            if hasattr(self, "updated_at") and self.updated_at
            else None,
        }
