from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    op_type: Mapped[str] = mapped_column(String(24), nullable=False)  # purchase/order/refund
    amount_rub: Mapped[int] = mapped_column(nullable=False, default=0)
    discount_rub: Mapped[int] = mapped_column(nullable=False, default=0)
    referral_discount_rub: Mapped[int] = mapped_column(nullable=False, default=0)
    comment: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_operations_salon_created", "salon_id", "created_at"),
        Index("ix_operations_salon_client_created", "salon_id", "client_id", "created_at"),
        Index("ix_operations_salon_type_created", "salon_id", "op_type", "created_at"),
    )
