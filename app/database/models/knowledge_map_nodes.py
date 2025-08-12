from datetime import datetime
from typing import Any, List
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class KnowledgeNodeModel(Base):
    __tablename__ = "KNOWLEDGE_NODES"

    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column("USER_ID", String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column("NAME", Text, nullable=False)

    documents = relationship(
        "NodeDocumentModel", back_populates="node", cascade="all, delete-orphan"
    )
    source_edges = relationship(
        "KnowledgeEdgeModel",
        back_populates="source",
        foreign_keys="KnowledgeEdgeModel.source_node_id",
        cascade="all, delete-orphan",
    )
    target_edges = relationship(
        "KnowledgeEdgeModel",
        back_populates="target",
        foreign_keys="KnowledgeEdgeModel.target_node_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("USER_ID", "NAME", name="UQ_KNOWLEDGE_NODES_USER_NAME"),
        Index("IX_KNOWLEDGE_NODES_USER", "USER_ID"),
    )

    def __init__(self, **kw: Any):
        now = datetime.now()
        kwargs = {k: v for k, v in kw.items() if k in self.__dir__()}
        super().__init__(**kwargs, created_at=now, updated_at=now)
        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "kn"  # knowledge node

    def get_identifiers(self) -> List[Any]:
        # use user_id + name to keep it deterministic
        return [self.user_id, self.name]
