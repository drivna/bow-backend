from datetime import datetime
from typing import Any, List
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class NodeDocumentModel(Base):
    __tablename__ = "NODE_DOCUMENTS"

    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)

    node_id: Mapped[str] = mapped_column(
        "NODE_ID",
        String(100),
        ForeignKey("KNOWLEDGE_NODES.ID", ondelete="CASCADE"),
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
    page_number: Mapped[int | None] = mapped_column("PAGE_NUMBER", String(32), nullable=True)

    node = relationship("KnowledgeNodeModel", back_populates="documents")

    __table_args__ = (
        UniqueConstraint("NODE_ID", "FILE_ID", name="UQ_NODE_DOCUMENTS_NODE_FILE"),
        Index("IX_NODE_DOCUMENTS_NODE", "NODE_ID"),
        Index("IX_NODE_DOCUMENTS_FILE", "FILE_ID"),
    )

    def __init__(self, **kw: Any):
        now = datetime.now()
        kwargs = {k: v for k, v in kw.items() if k in self.__dir__()}
        super().__init__(**kwargs, created_at=now, updated_at=now)
        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "nd"  # node-document

    def get_identifiers(self) -> List[Any]:
        return [self.node_id, self.file_id]
