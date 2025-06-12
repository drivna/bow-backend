from datetime import datetime
from typing import Any, List
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserModel(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    user_name: Mapped[str] = mapped_column(
        "USER_NAME",
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        "USER_EMAIL",
        String(255),
        nullable=False,
    )
    password: Mapped[str] = mapped_column(
        "PASSWORD",
        String(255),
        nullable=False,
    )

    __tablename__ = "USERS"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "user"

    def get_identifiers(self) -> List[Any]:
        return [self.email]
