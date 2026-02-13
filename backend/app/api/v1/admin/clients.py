from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.clients import (
    ClientCardOut,
    ClientCreateRequest,
    ClientGroupRuleInput,
    ClientGroupRuleOut,
    ClientGroupRulesResponse,
    ClientListResponse,
    ClientOut,
    ClientUpdateRequest,
)
from app.services.clients_service import (
    client_to_dict,
    create_client,
    get_client,
    get_client_card,
    list_clients,
    list_group_rules,
    render_clients_export_csv,
    replace_group_rules,
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
        whatsapp_phone=req.whatsapp_phone,
        email=str(req.email or ""),
        telegram_username=req.telegram_username,
        vk_username=req.vk_username,
        instagram_username=req.instagram_username,
        facebook_username=req.facebook_username,
        max_username=req.max_username,
        address=req.address,
        birthday=req.birthday,
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
        children=[x.model_dump() for x in req.children],
        loyalty_programs=[x.model_dump() for x in req.loyalty_programs],
    )
    return ClientOut(**client_to_dict(db, row))


@router.get("/export.csv", response_class=PlainTextResponse)
def get_export_csv(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    payload = render_clients_export_csv(db, salon_id=ctx.salon_id)
    return PlainTextResponse(
        content=payload,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clients_export.csv"},
    )


@router.get("/groups/rules", response_model=ClientGroupRulesResponse)
def get_group_rules(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ClientGroupRulesResponse:
    rows = list_group_rules(db, salon_id=ctx.salon_id)
    return ClientGroupRulesResponse(items=[ClientGroupRuleOut(
            id=x.id,
            group_name=x.group_name,
            is_active=x.is_active,
            min_visits=x.min_visits,
            min_total_spent_rub=x.min_total_spent_rub,
            inactive_days_over=x.inactive_days_over,
            require_marketing_consent=x.require_marketing_consent,
        ) for x in rows])


@router.put("/groups/rules", response_model=ClientGroupRulesResponse)
def put_group_rules(
    req: list[ClientGroupRuleInput],
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ClientGroupRulesResponse:
    rows = replace_group_rules(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        rules=[x.model_dump() for x in req],
    )
    return ClientGroupRulesResponse(items=[ClientGroupRuleOut(
            id=x.id,
            group_name=x.group_name,
            is_active=x.is_active,
            min_visits=x.min_visits,
            min_total_spent_rub=x.min_total_spent_rub,
            inactive_days_over=x.inactive_days_over,
            require_marketing_consent=x.require_marketing_consent,
        ) for x in rows])


@router.get("/{client_id}", response_model=ClientOut)
def get_client_by_id(
    client_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ClientOut:
    row = get_client(db, salon_id=ctx.salon_id, client_id=client_id)
    return ClientOut(**client_to_dict(db, row))


@router.get("/{client_id}/card", response_model=ClientCardOut)
def get_client_full_card(
    client_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ClientCardOut:
    return ClientCardOut(**get_client_card(db, salon_id=ctx.salon_id, client_id=client_id))


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
        whatsapp_phone=req.whatsapp_phone,
        email=str(req.email) if req.email is not None else None,
        telegram_username=req.telegram_username,
        vk_username=req.vk_username,
        instagram_username=req.instagram_username,
        facebook_username=req.facebook_username,
        max_username=req.max_username,
        address=req.address,
        birthday=req.birthday,
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
        children=[x.model_dump() for x in req.children] if req.children is not None else None,
        loyalty_programs=[x.model_dump() for x in req.loyalty_programs] if req.loyalty_programs is not None else None,
    )
    return ClientOut(**client_to_dict(db, row))
