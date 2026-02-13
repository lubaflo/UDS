from __future__ import annotations

import csv
import io
import time

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    Client,
    ClientActivity,
    ClientAnalytics,
    ClientChild,
    ClientGroupRule,
    ClientLoyaltyProgram,
    Operation,
)
from app.services.security_service import write_audit


def _tags_to_csv(tags: list[str]) -> str:
    clean = [t.strip() for t in tags if t.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for tag in clean:
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(tag)
    return ",".join(out)


def _csv_to_tags(csv_text: str) -> list[str]:
    if not csv_text:
        return []
    return [x.strip() for x in csv_text.split(",") if x.strip()]


def _get_client_analytics(db: Session, salon_id: int, client_id: int) -> ClientAnalytics | None:
    return db.execute(
        select(ClientAnalytics).where(
            ClientAnalytics.salon_id == salon_id,
            ClientAnalytics.client_id == client_id,
        )
    ).scalar_one_or_none()


def _sync_children(db: Session, salon_id: int, client_id: int, children: list[dict]) -> None:
    db.execute(
        delete(ClientChild).where(ClientChild.salon_id == salon_id, ClientChild.client_id == client_id)
    )
    for child in children:
        db.add(
            ClientChild(
                salon_id=salon_id,
                client_id=client_id,
                full_name=child["full_name"],
                birth_date=child["birth_date"],
                notes=child["notes"],
            )
        )


def _sync_loyalty_programs(db: Session, salon_id: int, client_id: int, loyalty_programs: list[dict]) -> None:
    db.execute(
        delete(ClientLoyaltyProgram).where(
            ClientLoyaltyProgram.salon_id == salon_id,
            ClientLoyaltyProgram.client_id == client_id,
        )
    )
    for program in loyalty_programs:
        db.add(
            ClientLoyaltyProgram(
                salon_id=salon_id,
                client_id=client_id,
                program_name=program["program_name"],
                status=program["status"],
                level_name=program["level_name"],
                balance=program["balance"],
                expires_at=program["expires_at"],
            )
        )


def _compute_groups(row: Client, rules: list[ClientGroupRule], now_ts: int) -> list[str]:
    groups: list[str] = []
    for rule in rules:
        if not rule.is_active:
            continue
        if row.visits_count < rule.min_visits:
            continue
        if row.total_spent_rub < rule.min_total_spent_rub:
            continue
        if rule.require_marketing_consent and not row.consent_marketing:
            continue
        if rule.inactive_days_over > 0:
            if not row.last_visit_at:
                continue
            inactive_days = int((now_ts - row.last_visit_at) / 86400)
            if inactive_days <= rule.inactive_days_over:
                continue
        groups.append(rule.group_name)
    return groups


def client_to_dict(db: Session, row: Client) -> dict:
    analytics = _get_client_analytics(db, row.salon_id, row.id)
    return {
        "id": row.id,
        "tg_id": row.tg_id,
        "username": row.username,
        "full_name": row.full_name,
        "phone": row.phone,
        "whatsapp_phone": row.whatsapp_phone,
        "email": row.email,
        "telegram_username": row.telegram_username,
        "vk_username": row.vk_username,
        "instagram_username": row.instagram_username,
        "facebook_username": row.facebook_username,
        "max_username": row.max_username,
        "address": row.address,
        "birthday": row.birthday,
        "status": row.status,
        "notes": row.notes,
        "tags": _csv_to_tags(row.tags_csv),
        "acquisition_channel_id": row.acquisition_channel_id,
        "visits_count": row.visits_count,
        "total_spent_rub": row.total_spent_rub,
        "last_visit_at": row.last_visit_at,
        "gender": analytics.gender if analytics else "unknown",
        "birth_year": analytics.birth_year if analytics else None,
        "consent_personal_data": row.consent_personal_data,
        "consent_marketing": row.consent_marketing,
        "consent_sms": row.consent_sms,
        "consent_app_push": row.consent_app_push,
        "consent_email": row.consent_email,
    }


def list_clients(db: Session, *, salon_id: int, query: str | None, page: int, page_size: int):
    q = select(Client).where(Client.salon_id == salon_id)
    if query:
        like = f"%{query.strip()}%"
        q = q.where(
            or_(
                Client.full_name.ilike(like),
                Client.phone.ilike(like),
                Client.whatsapp_phone.ilike(like),
                Client.email.ilike(like),
                Client.notes.ilike(like),
                Client.address.ilike(like),
                Client.username.ilike(like),
                Client.telegram_username.ilike(like),
                Client.vk_username.ilike(like),
                Client.instagram_username.ilike(like),
                Client.facebook_username.ilike(like),
                Client.max_username.ilike(like),
            )
        )
    q = q.order_by(Client.id.desc())
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    items = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, int(total)


def get_client(db: Session, *, salon_id: int, client_id: int) -> Client:
    return db.execute(
        select(Client).where(Client.salon_id == salon_id, Client.id == client_id)
    ).scalar_one()


def get_or_create_client_by_tg_id(
    db: Session,
    *,
    salon_id: int,
    tg_id: int,
    username: str,
    full_name: str,
) -> Client:
    row = db.execute(select(Client).where(Client.salon_id == salon_id, Client.tg_id == tg_id)).scalar_one_or_none()
    if row:
        if username and row.username != username:
            row.username = username
        if full_name and row.full_name != full_name:
            row.full_name = full_name
        return row

    row = Client(
        salon_id=salon_id,
        tg_id=tg_id,
        username=username,
        telegram_username=username,
        full_name=full_name or f"Telegram {tg_id}",
    )
    db.add(row)
    db.flush()
    db.add(
        ClientAnalytics(
            salon_id=salon_id,
            client_id=row.id,
            created_at=int(time.time()),
            gender="unknown",
            birth_year=None,
        )
    )
    return row


def create_client(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    tg_id: int | None,
    username: str,
    full_name: str,
    phone: str,
    whatsapp_phone: str,
    email: str,
    telegram_username: str,
    vk_username: str,
    instagram_username: str,
    facebook_username: str,
    max_username: str,
    address: str,
    birthday: str,
    notes: str,
    tags: list[str],
    acquisition_channel_id: int | None,
    gender: str,
    birth_year: int | None,
    consent_personal_data: bool,
    consent_marketing: bool,
    consent_sms: bool,
    consent_app_push: bool,
    consent_email: bool,
    children: list[dict],
    loyalty_programs: list[dict],
) -> Client:
    row = Client(
        salon_id=salon_id,
        tg_id=tg_id,
        username=username,
        full_name=full_name,
        phone=phone,
        whatsapp_phone=whatsapp_phone,
        email=email,
        telegram_username=telegram_username,
        vk_username=vk_username,
        instagram_username=instagram_username,
        facebook_username=facebook_username,
        max_username=max_username,
        address=address,
        birthday=birthday,
        notes=notes,
        tags_csv=_tags_to_csv(tags),
        acquisition_channel_id=acquisition_channel_id,
        consent_personal_data=consent_personal_data,
        consent_marketing=consent_marketing,
        consent_sms=consent_sms,
        consent_app_push=consent_app_push,
        consent_email=consent_email,
    )
    db.add(row)
    db.flush()

    db.add(
        ClientAnalytics(
            salon_id=salon_id,
            client_id=row.id,
            created_at=int(time.time()),
            gender=gender,
            birth_year=birth_year,
        )
    )
    _sync_children(db, salon_id, row.id, children)
    _sync_loyalty_programs(db, salon_id, row.id, loyalty_programs)

    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="client.create",
        entity="client",
        entity_id=str(row.id),
    )
    return row


def update_client(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    client_id: int,
    username: str | None,
    full_name: str | None,
    phone: str | None,
    whatsapp_phone: str | None,
    email: str | None,
    telegram_username: str | None,
    vk_username: str | None,
    instagram_username: str | None,
    facebook_username: str | None,
    max_username: str | None,
    address: str | None,
    birthday: str | None,
    status: str | None,
    notes: str | None,
    tags: list[str] | None,
    acquisition_channel_id: int | None,
    gender: str | None,
    birth_year: int | None,
    consent_personal_data: bool | None,
    consent_marketing: bool | None,
    consent_sms: bool | None,
    consent_app_push: bool | None,
    consent_email: bool | None,
    children: list[dict] | None,
    loyalty_programs: list[dict] | None,
) -> Client:
    row = get_client(db, salon_id=salon_id, client_id=client_id)
    analytics = _get_client_analytics(db, salon_id, client_id)
    if analytics is None:
        analytics = ClientAnalytics(
            salon_id=salon_id,
            client_id=client_id,
            created_at=int(time.time()),
            gender="unknown",
            birth_year=None,
        )
        db.add(analytics)
        db.flush()

    changed: list[str] = []
    updates = {
        "username": username,
        "full_name": full_name,
        "phone": phone,
        "whatsapp_phone": whatsapp_phone,
        "email": email,
        "telegram_username": telegram_username,
        "vk_username": vk_username,
        "instagram_username": instagram_username,
        "facebook_username": facebook_username,
        "max_username": max_username,
        "address": address,
        "birthday": birthday,
        "status": status,
        "notes": notes,
        "consent_personal_data": consent_personal_data,
        "consent_marketing": consent_marketing,
        "consent_sms": consent_sms,
        "consent_app_push": consent_app_push,
        "consent_email": consent_email,
    }
    for field, value in updates.items():
        if value is not None and value != getattr(row, field):
            setattr(row, field, value)
            changed.append(field)

    if tags is not None:
        csv_tags = _tags_to_csv(tags)
        if csv_tags != row.tags_csv:
            row.tags_csv = csv_tags
            changed.append("tags")

    if acquisition_channel_id is not None and acquisition_channel_id != row.acquisition_channel_id:
        row.acquisition_channel_id = acquisition_channel_id
        changed.append("acquisition_channel_id")

    if gender is not None and gender != analytics.gender:
        analytics.gender = gender
        changed.append("gender")

    if birth_year is not None and birth_year != analytics.birth_year:
        analytics.birth_year = birth_year
        changed.append("birth_year")

    if children is not None:
        _sync_children(db, salon_id, client_id, children)
        changed.append("children")

    if loyalty_programs is not None:
        _sync_loyalty_programs(db, salon_id, client_id, loyalty_programs)
        changed.append("loyalty_programs")

    if changed:
        write_audit(
            db,
            salon_id=salon_id,
            actor_user_id=actor_user_id,
            action="client.update",
            entity="client",
            entity_id=str(client_id),
            meta_json=",".join(changed),
        )
    return row


def get_client_activity(
    db: Session,
    *,
    salon_id: int,
    client_id: int,
    page: int,
    page_size: int,
) -> tuple[list[ClientActivity], int]:
    q = (
        select(ClientActivity)
        .where(ClientActivity.salon_id == salon_id, ClientActivity.client_id == client_id)
        .order_by(ClientActivity.created_at.desc())
    )
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    items = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, int(total)


def get_client_card(db: Session, *, salon_id: int, client_id: int) -> dict:
    now_ts = int(time.time())
    row = get_client(db, salon_id=salon_id, client_id=client_id)
    rules = db.execute(select(ClientGroupRule).where(ClientGroupRule.salon_id == salon_id)).scalars().all()
    children = db.execute(
        select(ClientChild).where(ClientChild.salon_id == salon_id, ClientChild.client_id == client_id)
    ).scalars().all()
    loyalty = db.execute(
        select(ClientLoyaltyProgram).where(
            ClientLoyaltyProgram.salon_id == salon_id,
            ClientLoyaltyProgram.client_id == client_id,
        )
    ).scalars().all()
    visits = db.execute(
        select(Appointment)
        .where(Appointment.salon_id == salon_id, Appointment.client_id == client_id)
        .order_by(Appointment.starts_at.desc())
    ).scalars().all()
    purchases = db.execute(
        select(Operation)
        .where(Operation.salon_id == salon_id, Operation.client_id == client_id)
        .order_by(Operation.created_at.desc())
    ).scalars().all()

    return {
        "client": client_to_dict(db, row),
        "groups": _compute_groups(row, rules, now_ts),
        "children": [
            {"id": x.id, "full_name": x.full_name, "birth_date": x.birth_date, "notes": x.notes}
            for x in children
        ],
        "loyalty_programs": [
            {
                "id": x.id,
                "program_name": x.program_name,
                "status": x.status,
                "level_name": x.level_name,
                "balance": x.balance,
                "expires_at": x.expires_at,
            }
            for x in loyalty
        ],
        "visit_history": [{"id": x.id, "title": x.title, "starts_at": x.starts_at, "status": x.status} for x in visits],
        "purchase_history": [
            {
                "id": x.id,
                "op_type": x.op_type,
                "amount_rub": x.amount_rub,
                "discount_rub": x.discount_rub,
                "referral_discount_rub": x.referral_discount_rub,
                "comment": x.comment,
                "created_at": x.created_at,
            }
            for x in purchases
        ],
    }


def list_group_rules(db: Session, *, salon_id: int) -> list[ClientGroupRule]:
    return db.execute(
        select(ClientGroupRule).where(ClientGroupRule.salon_id == salon_id).order_by(ClientGroupRule.id.asc())
    ).scalars().all()


def replace_group_rules(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    rules: list[dict],
) -> list[ClientGroupRule]:
    db.execute(delete(ClientGroupRule).where(ClientGroupRule.salon_id == salon_id))
    for rule in rules:
        db.add(ClientGroupRule(salon_id=salon_id, **rule))
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="client.group_rules.replace",
        entity="client_group_rule",
        entity_id=str(salon_id),
    )
    db.flush()
    return list_group_rules(db, salon_id=salon_id)


def render_clients_export_csv(db: Session, *, salon_id: int) -> str:
    clients = db.execute(select(Client).where(Client.salon_id == salon_id).order_by(Client.id.asc())).scalars().all()
    rules = list_group_rules(db, salon_id=salon_id)
    now_ts = int(time.time())

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "full_name",
            "phone",
            "whatsapp_phone",
            "telegram_username",
            "vk_username",
            "instagram_username",
            "email",
            "birthday",
            "children",
            "consent_personal_data",
            "consent_marketing",
            "consent_sms",
            "consent_app_push",
            "consent_email",
            "visits_count",
            "total_spent_rub",
            "last_visit_at",
            "groups",
            "loyalty_programs",
        ]
    )
    for client in clients:
        children = db.execute(
            select(ClientChild.full_name).where(
                ClientChild.salon_id == salon_id,
                ClientChild.client_id == client.id,
            )
        ).scalars().all()
        loyalty = db.execute(
            select(ClientLoyaltyProgram.program_name).where(
                ClientLoyaltyProgram.salon_id == salon_id,
                ClientLoyaltyProgram.client_id == client.id,
            )
        ).scalars().all()
        groups = _compute_groups(client, rules, now_ts)
        writer.writerow(
            [
                client.id,
                client.full_name,
                client.phone,
                client.whatsapp_phone,
                client.telegram_username,
                client.vk_username,
                client.instagram_username,
                client.email,
                client.birthday,
                "; ".join(children),
                client.consent_personal_data,
                client.consent_marketing,
                client.consent_sms,
                client.consent_app_push,
                client.consent_email,
                client.visits_count,
                client.total_spent_rub,
                client.last_visit_at or "",
                "; ".join(groups),
                "; ".join(loyalty),
            ]
        )
    return buf.getvalue()
