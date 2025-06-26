from datetime import datetime
from enum import Enum
from typing import Any, List
from sqlalchemy import ForeignKey, String, Enum as sqlEnum, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class QuestionSource(Enum):
    FLASHCARDS = "FLASHCARDS"


class QNAModel(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    source: Mapped[QuestionSource] = mapped_column(
        "SOURCE",
        sqlEnum(QuestionSource),
        nullable=False,
    )
    source_id: Mapped[str] = mapped_column("SOURCE_ID", String(100), index=True)

    question: Mapped[str] = mapped_column(
        "QUESTION",
        Text,
        nullable=False,
    )

    answer: Mapped[str] = mapped_column("ANSWER", Text, nullable=False)

    __tablename__ = "QNA"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "qna"

    def get_identifiers(self) -> List[Any]:
        return [self.source, self.source_id, self.created_at]
