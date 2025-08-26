from datetime import datetime
from typing import Any, List
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ChatModel(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        "USER_ID",
        String(255),
        ForeignKey("USERS.ID"),
        nullable=False,
        index=True,
    )

    message: Mapped[str] = mapped_column(
        "MESSAGE",
        Text,
        nullable=False,
    )
    is_from_system: Mapped[bool] = mapped_column(
        "IS_FROM_SYSTEM", Boolean, nullable=False, default=True
    )
    __tablename__ = "CHATS"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "chat"

    def get_identifiers(self) -> List[Any]:
        return [self.user_id, self.message, self.is_from_system, self.created_at]
