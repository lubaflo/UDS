from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Paginated


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    unit: str
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
    is_promo: bool | None = None
    price_rub: int | None = Field(default=None, ge=0)
    sku: str | None = Field(default=None, max_length=64)
    stock: int | None = Field(default=None, ge=0)
    images: list[str] | None = Field(default=None, max_length=6)
