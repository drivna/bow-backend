from datetime import datetime
from enum import Enum
from typing import Any, List
from sqlalchemy import ForeignKey, String, Enum as sqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class QnaFlashCardAction(Enum):
    KNOWN = "KNOWN"
    REVIEW_LATER = "REVIEW_LATER"


class QNAActions(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)

    qna_id: Mapped[str] = mapped_column(  # created by user
        "QNA_ID",
        String(255),
        ForeignKey("QNA.ID"),
        nullable=False,
        index=True,
    )
    qna_flashcard_action: Mapped[QnaFlashCardAction] = mapped_column(
        "FLASHCARD_ACTION",
        sqlEnum(QnaFlashCardAction),
        nullable=False,
    )

    __tablename__ = "QNA_ACTION"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "qnaction"

    def get_identifiers(self) -> List[Any]:
        return [self.qna_id]
