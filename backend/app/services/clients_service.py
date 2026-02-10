from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Client
from app.services.security_service import write_audit


def _tags_to_csv(tags: list[str]) -> str:
    clean = [t.strip() for t in tags if t and t.strip()]
    # unique preserve order
    seen = set()
    out: list[str] = []
    for t in clean:
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        out.append(t)
    return ",".join(out)


def _csv_to_tags(csv: str) -> list[str]:
    if not csv:
        return []
    return [x.strip() for x in csv.split(",") if x.strip()]


def list_clients(
    db: Session,
    *,
    salon_id: int,
    query: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Client], int]:
    q = select(Client).where(Client.salon_id == salon_id)

    if query:
        like = f"%{query.strip()}%"
        q = q.where(or_(Client.name.ilike(like), Client.phone.ilike(like), Client.notes.ilike(like)))

    q = q.order_by(Client.id.desc())
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    items = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, int(total)


def get_client(db: Session, *, salon_id: int, client_id: int) -> Client:
    row = db.execute(
        select(Client).where(Client.salon_id == salon_id, Client.id == client_id)
    ).scalar_one()
    return row


def update_client(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    client_id: int,
    name: str | None,
    phone: str | None,
    status: str | None,
    notes: str | None,
) -> Client:
    row = get_client(db, salon_id=salon_id, client_id=client_id)
    changed: list[str] = []

    if name is not None and name != row.name:
        row.name = name
        changed.append("name")
    if phone is not None and phone != row.phone:
        row.phone = phone
        changed.append("phone")
    if status is not None and status != row.status:
        row.status = status
        changed.append("status")
    if notes is not None and notes != row.notes:
        row.notes = notes
        changed.append("notes")

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


def set_client_tags(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    client_id: int,
    tags: list[str],
) -> Client:
    row = get_client(db, salon_id=salon_id, client_id=client_id)
    row.tags_csv = _tags_to_csv(tags)
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="client.tags.set",
        entity="client",
        entity_id=str(client_id),
        meta_json=row.tags_csv,
    )
    return row


def client_to_dict(row: Client) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "phone": row.phone,
        "status": row.status,
        "tags": _csv_to_tags(row.tags_csv),
        "notes": row.notes,
        "visits_count": row.visits_count,
        "total_spent_rub": row.total_spent_rub,
        "last_visit_at": row.last_visit_at,
    }