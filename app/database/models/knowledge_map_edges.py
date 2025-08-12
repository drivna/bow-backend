from datetime import datetime
from typing import Any, List
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class KnowledgeEdgeModel(Base):
    __tablename__ = "KNOWLEDGE_EDGES"

    id: Mapped[str] = mapped_column("ID", String(100), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column("USER_ID", String(100), nullable=False, index=True)

    source_node_id: Mapped[str] = mapped_column(
        "SOURCE_NODE_ID",
        String(100),
        ForeignKey("KNOWLEDGE_NODES.ID", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[str] = mapped_column(
        "TARGET_NODE_ID",
        String(100),
        ForeignKey("KNOWLEDGE_NODES.ID", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    weight: Mapped[str | None] = mapped_column("WEIGHT", String(32), nullable=True)

    source = relationship(
        "KnowledgeNodeModel", foreign_keys=[source_node_id], back_populates="source_edges"
    )
    target = relationship(
        "KnowledgeNodeModel", foreign_keys=[target_node_id], back_populates="target_edges"
    )

    __table_args__ = (
        UniqueConstraint(
            "USER_ID", "SOURCE_NODE_ID", "TARGET_NODE_ID", name="UQ_KNOWLEDGE_EDGES_USER_PAIR"
        ),
        Index("IX_KNOWLEDGE_EDGES_USER", "USER_ID"),
    )

    def __init__(self, **kw: Any):
        now = datetime.now()
        kwargs = {k: v for k, v in kw.items() if k in self.__dir__()}
        super().__init__(**kwargs, created_at=now, updated_at=now)
        super().__init__(id=self.compute_and_get_id())

    def token(self) -> str:
        return "ke"  # knowledge edge

    def get_identifiers(self) -> List[Any]:
        # normalize order in your service before constructing
        return [self.user_id, self.source_node_id, self.target_node_id]
