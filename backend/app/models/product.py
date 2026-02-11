from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(5000), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Без категории")
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="Штуки")
    is_promo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price_rub: Mapped[int] = mapped_column(nullable=False, default=0)
    sku: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[int] = mapped_column(nullable=False)
    updated_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_products_salon_name", "salon_id", "name"),
        Index("ix_products_salon_category", "salon_id", "category"),
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        Index("ix_product_images_product_sort", "product_id", "sort_order"),
    )
