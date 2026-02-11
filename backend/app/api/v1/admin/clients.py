from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.clients import ClientCreateRequest, ClientListResponse, ClientOut, ClientUpdateRequest
from app.services.clients_service import (
    client_to_dict,
    create_client,
    get_client,
    list_clients,
    update_client,
)

router = APIRouter(prefix="/admin/clients", tags=["admin.clients"])


@router.get("", response_model=ClientListResponse)
def get_clients(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ClientListResponse:
    items, total = list_clients(db, salon_id=ctx.salon_id, query=q, page=page, page_size=page_size)
    return ClientListResponse(
        items=[ClientOut(**client_to_dict(db, x)) for x in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("", response_model=ClientOut)
def post_create_client(
    req: ClientCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ClientOut:
    row = create_client(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        tg_id=req.tg_id,
        username=req.username,
        full_name=req.full_name,
        phone=req.phone,
        email=str(req.email or ""),
        vk_username=req.vk_username,
        instagram_username=req.instagram_username,
        facebook_username=req.facebook_username,
        max_username=req.max_username,
        address=req.address,
        notes=req.notes,
        tags=req.tags,
        acquisition_channel_id=req.acquisition_channel_id,
        gender=req.gender,
        birth_year=req.birth_year,
        consent_personal_data=req.consent_personal_data,
        consent_marketing=req.consent_marketing,
        consent_sms=req.consent_sms,
        consent_app_push=req.consent_app_push,
        consent_email=req.consent_email,
    )
    return ClientOut(**client_to_dict(db, row))


@router.get("/{client_id}", response_model=ClientOut)
def get_client_by_id(
    client_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ClientOut:
    row = get_client(db, salon_id=ctx.salon_id, client_id=client_id)
    return ClientOut(**client_to_dict(db, row))


@router.put("/{client_id}", response_model=ClientOut)
def put_update_client(
    client_id: int,
    req: ClientUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ClientOut:
    row = update_client(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        client_id=client_id,
        username=req.username,
        full_name=req.full_name,
        phone=req.phone,
        email=str(req.email) if req.email is not None else None,
        vk_username=req.vk_username,
        instagram_username=req.instagram_username,
        facebook_username=req.facebook_username,
        max_username=req.max_username,
        address=req.address,
        status=req.status,
        notes=req.notes,
        tags=req.tags,
        acquisition_channel_id=req.acquisition_channel_id,
        gender=req.gender,
        birth_year=req.birth_year,
        consent_personal_data=req.consent_personal_data,
        consent_marketing=req.consent_marketing,
        consent_sms=req.consent_sms,
        consent_app_push=req.consent_app_push,
        consent_email=req.consent_email,
    )
    return ClientOut(**client_to_dict(db, row))
