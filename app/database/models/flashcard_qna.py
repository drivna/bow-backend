from datetime import datetime
from typing import Any, List
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class FlashCardQnAModel(Base):
    __tablename__ = "FLASHCARD_QNA"

    id: Mapped[str] = mapped_column("ID", String(100), ForeignKey("QNA.ID"), primary_key=True)

    flashcard_id: Mapped[str] = mapped_column(
        "FLASHCARD_ID",
        String(100),
        ForeignKey("FLASHCARDS.ID"),
        nullable=False,
        index=True,
    )

    # Relationship back to QNA
    qna = relationship("QNAModel", back_populates="flashcard_qna")

    # Relationship back to FlashCardModel
    flashcard = relationship("FlashCardModel", back_populates="flashcard_qna_items")

    def __init__(self, **kw: Any):
        current_time = datetime.now()
        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}
        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)
        super().__init__(**kwargs)

    def get_identifiers(self) -> List[Any]:
        return [self.flashcard_id, self.created_at]
