from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import (
    InventoryLocation,
    Product,
    ProductImage,
    ServiceSpecificationItem,
    StockBalance,
    StockMovement,
)
from app.schemas.products import (
    InventoryLocationCreateRequest,
    InventoryLocationOut,
    ProductCreateRequest,
    ProductListResponse,
    ProductOut,
    ProductStockSummaryOut,
    ProductUpdateRequest,
    ServiceSpecificationItemCreateRequest,
    ServiceSpecificationItemOut,
    StockByLocationOut,
    StockMovementCreateRequest,
    StockMovementListResponse,
    StockMovementOut,
)
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
        full_name=row.full_name,
        receipt_name=row.receipt_name,
        description=row.description,
        category=row.category,
        unit=row.unit,
        item_type=row.item_type,
        track_inventory=row.track_inventory,
        is_promo=row.is_promo,
        price_rub=row.price_rub,
        cost_price_rub=row.cost_price_rub,
        sku=row.sku,
        barcode=row.barcode,
        manufacturer=row.manufacturer,
        country_of_origin=row.country_of_origin,
        tax_rate_percent=row.tax_rate_percent,
        is_traceable=row.is_traceable,
        service_duration_min=row.service_duration_min,
        stock=row.stock,
        critical_stock=row.critical_stock,
        desired_stock=row.desired_stock,
        comment=row.comment,
        images=list(images),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _movement_out(db: Session, row: StockMovement) -> StockMovementOut:
    product_name = db.execute(select(Product.name).where(Product.id == row.product_id)).scalar_one()
    location_name = db.execute(select(InventoryLocation.name).where(InventoryLocation.id == row.location_id)).scalar_one()
    return StockMovementOut(
        id=row.id,
        product_id=row.product_id,
        product_name=product_name,
        location_id=row.location_id,
        location_name=location_name,
        movement_type=row.movement_type,
        quantity=row.quantity,
        unit_cost_rub=row.unit_cost_rub,
        total_cost_rub=row.total_cost_rub,
        counterparty=row.counterparty,
        comment=row.comment,
        occurred_at=row.occurred_at,
        created_at=row.created_at,
    )


def _service_spec_item_out(db: Session, row: ServiceSpecificationItem) -> ServiceSpecificationItemOut:
    material_name = db.execute(select(Product.name).where(Product.id == row.material_product_id)).scalar_one()
    return ServiceSpecificationItemOut(
        id=row.id,
        service_product_id=row.service_product_id,
        material_product_id=row.material_product_id,
        material_name=material_name,
        quantity=row.quantity,
        unit=row.unit,
        comment=row.comment,
    )


@router.get("", response_model=ProductListResponse)
def list_products(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    item_type: str | None = Query(default=None, pattern=r"^(product|service)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    query = select(Product).where(Product.salon_id == ctx.salon_id)
    if q:
        like = f"%{q.strip()}%"
        query = query.where(
            (Product.name.ilike(like))
            | (Product.full_name.ilike(like))
            | (Product.description.ilike(like))
            | (Product.sku.ilike(like))
            | (Product.barcode.ilike(like))
        )
    if category:
        query = query.where(Product.category == category)
    if item_type:
        query = query.where(Product.item_type == item_type)
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
    track_inventory = req.track_inventory if req.item_type == "product" else False
    row = Product(
        salon_id=ctx.salon_id,
        name=req.name,
        full_name=req.full_name,
        receipt_name=req.receipt_name,
        description=req.description,
        category=req.category,
        unit=req.unit,
        item_type=req.item_type,
        track_inventory=track_inventory,
        is_promo=req.is_promo,
        price_rub=req.price_rub,
        cost_price_rub=req.cost_price_rub,
        sku=req.sku,
        barcode=req.barcode,
        manufacturer=req.manufacturer,
        country_of_origin=req.country_of_origin,
        tax_rate_percent=req.tax_rate_percent,
        is_traceable=req.is_traceable,
        service_duration_min=req.service_duration_min,
        stock=req.stock,
        critical_stock=req.critical_stock,
        desired_stock=req.desired_stock,
        comment=req.comment,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    for idx, image in enumerate(req.images):
        db.add(ProductImage(product_id=row.id, image_url=image, sort_order=idx))

    if track_inventory and req.stock > 0:
        location = db.execute(
            select(InventoryLocation)
            .where(and_(InventoryLocation.salon_id == ctx.salon_id, InventoryLocation.is_active.is_(True)))
            .order_by(InventoryLocation.id.asc())
        ).scalars().first()
        if location is not None:
            db.add(StockBalance(salon_id=ctx.salon_id, product_id=row.id, location_id=location.id, quantity=req.stock))
            db.add(
                StockMovement(
                    salon_id=ctx.salon_id,
                    product_id=row.id,
                    location_id=location.id,
                    movement_type="income",
                    quantity=req.stock,
                    unit_cost_rub=req.cost_price_rub,
                    total_cost_rub=req.cost_price_rub * req.stock,
                    counterparty="",
                    comment="Начальный остаток при создании карточки",
                    occurred_at=now,
                    created_at=now,
                )
            )

    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="product.create", entity="product", entity_id=str(row.id))
    return _product_out(db, row)


@router.get("/locations", response_model=list[InventoryLocationOut])
def list_locations(
    include_archived: bool = Query(default=False),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> list[InventoryLocationOut]:
    query = select(InventoryLocation).where(InventoryLocation.salon_id == ctx.salon_id)
    if not include_archived:
        query = query.where(InventoryLocation.is_active.is_(True))
    query = query.order_by(InventoryLocation.id.asc())
    rows = db.execute(query).scalars().all()
    return [
        InventoryLocationOut(
            id=x.id,
            name=x.name,
            location_type=x.location_type,
            is_active=x.is_active,
            created_at=x.created_at,
            updated_at=x.updated_at,
        )
        for x in rows
    ]


@router.post("/locations", response_model=InventoryLocationOut)
def create_location(
    req: InventoryLocationCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> InventoryLocationOut:
    now = int(time.time())
    row = InventoryLocation(
        salon_id=ctx.salon_id,
        name=req.name,
        location_type=req.location_type,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="inventory.location.create", entity="inventory_location", entity_id=str(row.id))
    return InventoryLocationOut(
        id=row.id,
        name=row.name,
        location_type=row.location_type,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/movements", response_model=StockMovementListResponse)
def list_movements(
    product_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    movement_type: str | None = Query(default=None, pattern=r"^(income|expense|adjustment)$"),
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> StockMovementListResponse:
    query = select(StockMovement).where(StockMovement.salon_id == ctx.salon_id)
    if product_id is not None:
        query = query.where(StockMovement.product_id == product_id)
    if location_id is not None:
        query = query.where(StockMovement.location_id == location_id)
    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type)
    if date_from is not None:
        query = query.where(StockMovement.occurred_at >= date_from)
    if date_to is not None:
        query = query.where(StockMovement.occurred_at <= date_to)

    query = query.order_by(StockMovement.id.desc())
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    rows = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return StockMovementListResponse(
        items=[_movement_out(db, row) for row in rows],
        page=page,
        page_size=page_size,
        total=int(total),
    )


@router.get("/{product_id}/stock", response_model=ProductStockSummaryOut)
def get_stock_summary(
    product_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ProductStockSummaryOut:
    row = db.execute(
        select(Product).where(and_(Product.id == product_id, Product.salon_id == ctx.salon_id))
    ).scalar_one()

    balances = db.execute(
        select(StockBalance, InventoryLocation)
        .join(InventoryLocation, InventoryLocation.id == StockBalance.location_id)
        .where(and_(StockBalance.salon_id == ctx.salon_id, StockBalance.product_id == product_id))
        .order_by(InventoryLocation.name.asc())
    ).all()
    by_location = [
        StockByLocationOut(location_id=balance.location_id, location_name=location.name, quantity=balance.quantity)
        for balance, location in balances
    ]
    return ProductStockSummaryOut(product_id=row.id, total_stock=row.stock, by_location=by_location)


@router.post("/{product_id}/movements", response_model=StockMovementOut)
def create_stock_movement(
    product_id: int,
    req: StockMovementCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> StockMovementOut:
    product = db.execute(
        select(Product).where(and_(Product.id == product_id, Product.salon_id == ctx.salon_id))
    ).scalar_one()

    if product.item_type != "product" or not product.track_inventory:
        raise HTTPException(status_code=400, detail="Для услуг складской учет недоступен")

    location = db.execute(
        select(InventoryLocation).where(
            and_(InventoryLocation.id == req.location_id, InventoryLocation.salon_id == ctx.salon_id)
        )
    ).scalar_one_or_none()
    if location is None or not location.is_active:
        raise HTTPException(status_code=400, detail="Склад/точка не найдены или неактивны")

    balance = db.execute(
        select(StockBalance).where(
            and_(
                StockBalance.salon_id == ctx.salon_id,
                StockBalance.product_id == product_id,
                StockBalance.location_id == req.location_id,
            )
        )
    ).scalar_one_or_none()
    if balance is None:
        balance = StockBalance(
            salon_id=ctx.salon_id,
            product_id=product_id,
            location_id=req.location_id,
            quantity=0,
        )
        db.add(balance)
        db.flush()

    if req.movement_type == "income":
        delta = req.quantity
    elif req.movement_type == "expense":
        delta = -req.quantity
    else:
        delta = req.quantity - balance.quantity

    if balance.quantity + delta < 0:
        raise HTTPException(status_code=400, detail="Недостаточно остатка на выбранной точке")

    now = int(time.time())
    occurred_at = req.occurred_at or now

    balance.quantity += delta
    product.stock += delta
    product.updated_at = now

    movement = StockMovement(
        salon_id=ctx.salon_id,
        product_id=product_id,
        location_id=req.location_id,
        movement_type=req.movement_type,
        quantity=req.quantity,
        unit_cost_rub=req.unit_cost_rub,
        total_cost_rub=req.unit_cost_rub * req.quantity,
        counterparty=req.counterparty,
        comment=req.comment,
        occurred_at=occurred_at,
        created_at=now,
    )
    db.add(movement)
    db.flush()

    write_audit(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        action="inventory.movement.create",
        entity="stock_movement",
        entity_id=str(movement.id),
    )

    return _movement_out(db, movement)


@router.get("/{product_id}/specification", response_model=list[ServiceSpecificationItemOut])
def list_service_specification(
    product_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> list[ServiceSpecificationItemOut]:
    service = db.execute(
        select(Product).where(and_(Product.id == product_id, Product.salon_id == ctx.salon_id))
    ).scalar_one()
    if service.item_type != "service":
        raise HTTPException(status_code=400, detail="Спецификацию можно вести только для услуг")

    rows = db.execute(
        select(ServiceSpecificationItem)
        .where(
            and_(
                ServiceSpecificationItem.salon_id == ctx.salon_id,
                ServiceSpecificationItem.service_product_id == product_id,
            )
        )
        .order_by(ServiceSpecificationItem.id.asc())
    ).scalars().all()
    return [_service_spec_item_out(db, row) for row in rows]


@router.post("/{product_id}/specification", response_model=ServiceSpecificationItemOut)
def add_service_specification_item(
    product_id: int,
    req: ServiceSpecificationItemCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ServiceSpecificationItemOut:
    service = db.execute(
        select(Product).where(and_(Product.id == product_id, Product.salon_id == ctx.salon_id))
    ).scalar_one()
    if service.item_type != "service":
        raise HTTPException(status_code=400, detail="Спецификацию можно вести только для услуг")

    material = db.execute(
        select(Product).where(and_(Product.id == req.material_product_id, Product.salon_id == ctx.salon_id))
    ).scalar_one_or_none()
    if material is None or material.item_type != "product":
        raise HTTPException(status_code=400, detail="Расходник должен быть карточкой товара")

    existing = db.execute(
        select(ServiceSpecificationItem).where(
            and_(
                ServiceSpecificationItem.salon_id == ctx.salon_id,
                ServiceSpecificationItem.service_product_id == product_id,
                ServiceSpecificationItem.material_product_id == req.material_product_id,
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.quantity = req.quantity
        existing.unit = req.unit
        existing.comment = req.comment
        row = existing
    else:
        row = ServiceSpecificationItem(
            salon_id=ctx.salon_id,
            service_product_id=product_id,
            material_product_id=req.material_product_id,
            quantity=req.quantity,
            unit=req.unit,
            comment=req.comment,
        )
        db.add(row)
        db.flush()

    write_audit(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        action="service.specification.upsert",
        entity="service_specification_item",
        entity_id=str(row.id),
    )
    return _service_spec_item_out(db, row)


@router.delete("/{product_id}/specification/{item_id}")
def remove_service_specification_item(
    product_id: int,
    item_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    row = db.execute(
        select(ServiceSpecificationItem).where(
            and_(
                ServiceSpecificationItem.id == item_id,
                ServiceSpecificationItem.service_product_id == product_id,
                ServiceSpecificationItem.salon_id == ctx.salon_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Позиция спецификации не найдена")

    db.delete(row)
    write_audit(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        action="service.specification.delete",
        entity="service_specification_item",
        entity_id=str(item_id),
    )
    return {"ok": True}


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
        if key == "track_inventory" and row.item_type == "service" and value:
            raise HTTPException(status_code=400, detail="Для услуг нельзя включить складской учет")
        setattr(row, key, value)

    if row.item_type == "service":
        row.track_inventory = False

    row.updated_at = int(time.time())

    if images is not None:
        db.query(ProductImage).filter(ProductImage.product_id == row.id).delete()
        for idx, image in enumerate(images):
            db.add(ProductImage(product_id=row.id, image_url=image, sort_order=idx))

    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="product.update", entity="product", entity_id=str(row.id))
    return _product_out(db, row)
