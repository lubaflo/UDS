from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Paginated


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    unit: str
    item_type: str
    track_inventory: bool
    is_promo: bool
    price_rub: int
    sku: str
    stock: int
    images: list[str]
    created_at: int
    updated_at: int


class ProductListResponse(Paginated):
    items: list[ProductOut]


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=5000)
    category: str = Field(default="Без категории", max_length=100)
    unit: str = Field(default="Штуки", max_length=32)
    item_type: str = Field(default="product", pattern=r"^(product|service)$")
    track_inventory: bool = True
    is_promo: bool = False
    price_rub: int = Field(ge=0)
    sku: str = Field(default="", max_length=64)
    stock: int = Field(default=0, ge=0)
    images: list[str] = Field(default_factory=list, max_length=6)


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=100)
    unit: str | None = Field(default=None, max_length=32)
    item_type: str | None = Field(default=None, pattern=r"^(product|service)$")
    track_inventory: bool | None = None
    is_promo: bool | None = None
    price_rub: int | None = Field(default=None, ge=0)
    sku: str | None = Field(default=None, max_length=64)
    stock: int | None = Field(default=None, ge=0)
    images: list[str] | None = Field(default=None, max_length=6)


class InventoryLocationOut(BaseModel):
    id: int
    name: str
    location_type: str
    is_active: bool
    created_at: int
    updated_at: int


class InventoryLocationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location_type: str = Field(default="warehouse", pattern=r"^(warehouse|store|point)$")


class StockByLocationOut(BaseModel):
    location_id: int
    location_name: str
    quantity: int


class ProductStockSummaryOut(BaseModel):
    product_id: int
    total_stock: int
    by_location: list[StockByLocationOut]


class StockMovementCreateRequest(BaseModel):
    location_id: int
    movement_type: str = Field(pattern=r"^(income|expense|adjustment)$")
    quantity: int = Field(gt=0)
    unit_cost_rub: int = Field(default=0, ge=0)
    counterparty: str = Field(default="", max_length=200)
    comment: str = Field(default="", max_length=1000)
    occurred_at: int | None = None


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    location_id: int
    location_name: str
    movement_type: str
    quantity: int
    unit_cost_rub: int
    total_cost_rub: int
    counterparty: str
    comment: str
    occurred_at: int
    created_at: int


class StockMovementListResponse(Paginated):
    items: list[StockMovementOut]
