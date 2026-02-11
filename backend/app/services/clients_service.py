from __future__ import annotations

import time

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Client, ClientActivity, ClientAnalytics
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


def _csv_to_tags(csv: str) -> list[str]:
    if not csv:
        return []
    return [x.strip() for x in csv.split(",") if x.strip()]


def _get_client_analytics(db: Session, salon_id: int, client_id: int) -> ClientAnalytics | None:
    return db.execute(
        select(ClientAnalytics).where(
            ClientAnalytics.salon_id == salon_id,
            ClientAnalytics.client_id == client_id,
        )
    ).scalar_one_or_none()


def client_to_dict(db: Session, row: Client) -> dict:
    analytics = _get_client_analytics(db, row.salon_id, row.id)
    return {
        "id": row.id,
        "tg_id": row.tg_id,
        "username": row.username,
        "full_name": row.full_name,
        "phone": row.phone,
        "email": row.email,
        "address": row.address,
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
                Client.email.ilike(like),
                Client.notes.ilike(like),
                Client.address.ilike(like),
                Client.username.ilike(like),
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


def create_client(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    tg_id: int | None,
    username: str,
    full_name: str,
    phone: str,
    email: str,
    address: str,
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
) -> Client:
    row = Client(
        salon_id=salon_id,
        tg_id=tg_id,
        username=username,
        full_name=full_name,
        phone=phone,
        email=email,
        address=address,
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
    email: str | None,
    address: str | None,
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
        "email": email,
        "address": address,
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
        csv = _tags_to_csv(tags)
        if csv != row.tags_csv:
            row.tags_csv = csv
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
