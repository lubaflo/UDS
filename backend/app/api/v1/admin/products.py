from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Product, ProductImage
from app.schemas.products import ProductCreateRequest, ProductListResponse, ProductOut, ProductUpdateRequest
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/products", tags=["admin.products"])


def _product_out(db: Session, row: Product) -> ProductOut:
    images = db.execute(
        select(ProductImage.image_url)
        .where(ProductImage.product_id == row.id)
        .order_by(ProductImage.sort_order.asc())
    ).scalars().all()
    return ProductOut(
        id=row.id,
        name=row.name,
        description=row.description,
        category=row.category,
        unit=row.unit,
        is_promo=row.is_promo,
        price_rub=row.price_rub,
        sku=row.sku,
        stock=row.stock,
        images=list(images),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=ProductListResponse)
def list_products(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    query = select(Product).where(Product.salon_id == ctx.salon_id)
    if q:
        like = f"%{q.strip()}%"
        query = query.where((Product.name.ilike(like)) | (Product.description.ilike(like)) | (Product.sku.ilike(like)))
    if category:
        query = query.where(Product.category == category)
    query = query.order_by(Product.id.desc())

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return ProductListResponse(
        items=[_product_out(db, x) for x in items],
        page=page,
        page_size=page_size,
        total=int(total),
    )


@router.post("", response_model=ProductOut)
def create_product(
    req: ProductCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ProductOut:
    now = int(time.time())
    row = Product(
        salon_id=ctx.salon_id,
        name=req.name,
        description=req.description,
        category=req.category,
        unit=req.unit,
        is_promo=req.is_promo,
        price_rub=req.price_rub,
        sku=req.sku,
        stock=req.stock,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    for idx, image in enumerate(req.images):
        db.add(ProductImage(product_id=row.id, image_url=image, sort_order=idx))
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="product.create", entity="product", entity_id=str(row.id))
    return _product_out(db, row)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    req: ProductUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ProductOut:
    row = db.execute(
        select(Product).where(and_(Product.id == product_id, Product.salon_id == ctx.salon_id))
    ).scalar_one()

    payload = req.model_dump(exclude_unset=True)
    images = payload.pop("images", None)
    for key, value in payload.items():
        setattr(row, key, value)
    row.updated_at = int(time.time())

    if images is not None:
        db.query(ProductImage).filter(ProductImage.product_id == row.id).delete()
        for idx, image in enumerate(images):
            db.add(ProductImage(product_id=row.id, image_url=image, sort_order=idx))

    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="product.update", entity="product", entity_id=str(row.id))
    return _product_out(db, row)
