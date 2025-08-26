from datetime import datetime
from typing import Any, List
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FileChatModel(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        "USER_ID",
        String(255),
        ForeignKey("USERS.ID"),
        nullable=False,
        index=True,
    )
    chat_id: Mapped[str] = mapped_column(
        "CHAT_ID",
        String(255),
        ForeignKey("CHATS.ID"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[str] = mapped_column(
        "FILE_ID",
        String(255),
        ForeignKey("FILES.ID"),
        nullable=False,
        index=True,
    )

    __tablename__ = "FILE_CHATS"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "filechat"

    def get_identifiers(self) -> List[Any]:
        return [self.user_id, self.file_id, self.chat_id]
