from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import JSON, ForeignKey, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class NotificationModel(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        "USER_ID",
        String(255),
        ForeignKey("USERS.ID"),
        nullable=False,
        index=True,
    )
    description: Mapped[Dict[str, Any]] = mapped_column(
        "DESCRIPTION",
        JSON,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        "MESSAGE",
        String(255),
        nullable=False,
    )
    is_relayed: Mapped[bool] = mapped_column(
        "IS_RELAYED",
        Boolean,
        nullable=False,
        default=False,
    )

    __tablename__ = "NOTIFICATIONS"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "notif"

    def get_identifiers(self) -> List[Any]:
        return [self.user_id, self.description, self.message, self.is_relayed]
