from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ActivityModel(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(  # created by user
        "USER_ID",
        String(255),
        ForeignKey("USERS.ID"),
        nullable=False,
        index=True,
    )
    activity_type: Mapped[str] = mapped_column(
        "ACTIVITY_TYPE",
        String(255),
        nullable=False,
    )
    activity_item_id: Mapped[str] = mapped_column(
        "ACTIVITY_ITEM_ID",
        String(255),
        nullable=False,
    )
    activity_description: Mapped[Dict[Any, Any]] = mapped_column(
        "DESCRIPTION", JSON, nullable=False, default={}
    )

    __tablename__ = "ACTIVITY"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "act"

    def get_identifiers(self) -> List[Any]:
        return [self.user_id, self.activity_item_id, self.activity_type, self.created_at.date()]
