from datetime import datetime
from typing import Any, List
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FileTopicModel(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)

    file_id: Mapped[str] = mapped_column(
        "FILE_ID",
        String(255),
        ForeignKey("FILES.ID"),
        nullable=False,
        index=True,
    )
    page_number :  Mapped[str] = mapped_column(
        "PAGE_NUMBER",
        String(255),
        nullable=False,
    )
    topic_name : Mapped[str] = mapped_column(
        "TOPIC_NAME",
        Text,
        nullable=False,
    )
    topic_description : Mapped[str] = mapped_column(
        "TOPIC_DESCRIPTION",
        Text,
        nullable=False,
    )

    __tablename__ = "FILE_TOPICS"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "ft"

    def get_identifiers(self) -> List[Any]:
        return [self.file_id, self.topic_name]
