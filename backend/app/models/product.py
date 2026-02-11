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
    item_type: Mapped[str] = mapped_column(String(16), nullable=False, default="product")  # product/service
    track_inventory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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


class InventoryLocation(Base):
    __tablename__ = "inventory_locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location_type: Mapped[str] = mapped_column(String(24), nullable=False, default="warehouse")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[int] = mapped_column(nullable=False)
    updated_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_inventory_locations_salon_name", "salon_id", "name"),
    )


class StockBalance(Base):
    __tablename__ = "stock_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("inventory_locations.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        Index("ix_stock_balances_salon_product_location", "salon_id", "product_id", "location_id", unique=True),
        Index("ix_stock_balances_salon_location", "salon_id", "location_id"),
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("inventory_locations.id", ondelete="CASCADE"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(24), nullable=False)  # income/expense/adjustment
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_cost_rub: Mapped[int] = mapped_column(nullable=False, default=0)
    total_cost_rub: Mapped[int] = mapped_column(nullable=False, default=0)
    counterparty: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    comment: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    occurred_at: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_stock_movements_salon_created", "salon_id", "created_at"),
        Index("ix_stock_movements_salon_product_created", "salon_id", "product_id", "created_at"),
        Index("ix_stock_movements_salon_location_created", "salon_id", "location_id", "created_at"),
    )
