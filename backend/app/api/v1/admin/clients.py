from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.clients import ClientListResponse, ClientOut, ClientTagsRequest, ClientUpdateRequest
from app.services.clients_service import client_to_dict, list_clients, set_client_tags, update_client

router = APIRouter(prefix="/admin/clients", tags=["admin.clients"])


@router.get("", response_model=ClientListResponse)
def get_clients(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin", "operator", "staff")),
    db: Session = Depends(get_db),
) -> ClientListResponse:
    items, total = list_clients(db, salon_id=ctx.salon_id, query=q, page=page, page_size=page_size)
    return ClientListResponse(
        items=[ClientOut(**client_to_dict(x)) for x in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: int,
    ctx=Depends(require_roles("owner", "admin", "operator", "staff")),
    db: Session = Depends(get_db),
) -> ClientOut:
    from app.services.clients_service import get_client as _get

    row = _get(db, salon_id=ctx.salon_id, client_id=client_id)
    return ClientOut(**client_to_dict(row))


@router.post("/{client_id}", response_model=ClientOut)
def post_update_client(
    client_id: int,
    req: ClientUpdateRequest,
    ctx=Depends(require_roles("owner", "admin", "operator")),
    db: Session = Depends(get_db),
) -> ClientOut:
    row = update_client(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        client_id=client_id,
        name=req.name,
        phone=req.phone,
        status=req.status,
        notes=req.notes,
    )
    return ClientOut(**client_to_dict(row))


@router.post("/{client_id}/tags", response_model=ClientOut)
def post_set_tags(
    client_id: int,
    req: ClientTagsRequest,
    ctx=Depends(require_roles("owner", "admin", "operator")),
    db: Session = Depends(get_db),
) -> ClientOut:
    row = set_client_tags(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        client_id=client_id,
        tags=req.tags,
    )
    return ClientOut(**client_to_dict(row))