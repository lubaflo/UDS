from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import NewsEvent, NewsPost
from app.schemas.news import (
    NewsListResponse,
    NewsMetricOut,
    NewsPostCreateRequest,
    NewsPostOut,
    NewsPostUpdateRequest,
    NewsStatsOut,
    NewsTrackRequest,
)
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/news", tags=["admin.news"])


@router.get("", response_model=NewsListResponse)
def list_news(
    status: str | None = Query(default=None, pattern="^(active|archived|draft)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> NewsListResponse:
    q = select(NewsPost).where(NewsPost.salon_id == ctx.salon_id)
    if status:
        q = q.where(NewsPost.status == status)
    q = q.order_by(NewsPost.id.desc())
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return NewsListResponse(
        items=[NewsPostOut.model_validate(x, from_attributes=True) for x in rows],
        page=page,
        page_size=page_size,
        total=int(total),
    )


@router.post("", response_model=NewsPostOut)
def create_news(
    req: NewsPostCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> NewsPostOut:
    now = int(time.time())
    row = NewsPost(
        salon_id=ctx.salon_id,
        title=req.title,
        body=req.body,
        cover_image_url=req.cover_image_url,
        status=req.status,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="news.create", entity="news_post", entity_id=str(row.id))
    return NewsPostOut.model_validate(row, from_attributes=True)


@router.put("/{news_post_id}", response_model=NewsPostOut)
def update_news(
    news_post_id: int,
    req: NewsPostUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> NewsPostOut:
    row = db.execute(
        select(NewsPost).where(and_(NewsPost.id == news_post_id, NewsPost.salon_id == ctx.salon_id))
    ).scalar_one()

    if req.title is not None:
        row.title = req.title
    if req.body is not None:
        row.body = req.body
    if req.cover_image_url is not None:
        row.cover_image_url = req.cover_image_url
    if req.status is not None:
        row.status = req.status

    row.updated_at = int(time.time())
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="news.update", entity="news_post", entity_id=str(row.id))
    return NewsPostOut.model_validate(row, from_attributes=True)


@router.post("/track", response_model=NewsStatsOut)
def track_news_event(
    req: NewsTrackRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> NewsStatsOut:
    post = db.execute(
        select(NewsPost).where(and_(NewsPost.id == req.news_post_id, NewsPost.salon_id == ctx.salon_id))
    ).scalar_one()

    row = NewsEvent(
        salon_id=ctx.salon_id,
        news_post_id=post.id,
        event_type=req.event_type,
        client_id=req.client_id,
        source=req.source,
        occurred_at=req.occurred_at or int(time.time()),
    )
    db.add(row)
    db.flush()

    write_audit(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        action="news.track_event",
        entity="news_post",
        entity_id=str(post.id),
        meta_json=req.event_type,
    )
    return get_news_stats(news_post_id=post.id, ctx=ctx, db=db)


@router.get("/{news_post_id}/stats", response_model=NewsStatsOut)
def get_news_stats(
    news_post_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> NewsStatsOut:
    _ = db.execute(
        select(NewsPost).where(and_(NewsPost.id == news_post_id, NewsPost.salon_id == ctx.salon_id))
    ).scalar_one()

    metrics_q = (
        select(
            NewsEvent.event_type,
            func.count().label("count"),
            func.max(
                case(
                    (NewsEvent.event_type == "view", 1),
                    (NewsEvent.event_type == "transition", 2),
                    (NewsEvent.event_type == "click", 3),
                    (NewsEvent.event_type == "add_to_cart", 4),
                    (NewsEvent.event_type == "booking", 5),
                    (NewsEvent.event_type == "purchase", 6),
                    else_=99,
                )
            ).label("sort_order"),
        )
        .where(and_(NewsEvent.news_post_id == news_post_id, NewsEvent.salon_id == ctx.salon_id))
        .group_by(NewsEvent.event_type)
        .order_by("sort_order", NewsEvent.event_type)
    )
    rows = db.execute(metrics_q).all()

    metrics = [NewsMetricOut(event_type=event_type, count=count) for event_type, count, _ in rows]
    total_events = sum(item.count for item in metrics)
    return NewsStatsOut(news_post_id=news_post_id, total_events=total_events, metrics=metrics)
