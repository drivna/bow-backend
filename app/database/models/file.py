from datetime import datetime
from typing import Any, List
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FileModel(Base):
    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    uploaded_by: Mapped[str] = mapped_column(  # created by user
        "USER_ID",
        String(255),
        ForeignKey("USERS.ID"),
        nullable=False,
        index=True,
    )
    file_hash: Mapped[str] = mapped_column(
        "FILE_HASH",
        Text,
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(
        "FILE_NAME",
        String(255),
        nullable=False,
    )

    file_content: Mapped[str] = mapped_column(
        "FILE_CONTENT",
        Text,
        nullable=False,
    )
    file_type = mapped_column(
        "FILE_TYPE",
        String(255),
        nullable=False,
    )

    __tablename__ = "FILES"

    def __init__(self, **kw: Any):
        current_time = datetime.now()

        kwargs = {key: value for key, value in kw.items() if key in self.__dir__()}

        super().__init__(**kwargs, created_at=current_time, updated_at=current_time)

        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "file"

    def get_identifiers(self) -> List[Any]:
        return [self.uploaded_by, self.file_hash, self.file_type]
