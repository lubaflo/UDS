from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import AppPageEvent, Client, ClientAnalytics, Feedback, Operation
from app.schemas.analytics import (
    AppVisitsAnalyticsResponse,
    CustomersAnalyticsResponse,
    DistributionItem,
    LevelsAnalyticsItem,
    LevelsAnalyticsResponse,
    MetricCard,
    OperationsAnalyticsResponse,
    RatingAnalyticsResponse,
    SeriesPoint,
)

router = APIRouter(prefix="/admin/analytics", tags=["admin.analytics"])


def _range_bounds(date_from: int | None, date_to: int | None) -> tuple[int, int]:
    now = int(time.time())
    end_ts = date_to if date_to is not None else now
    start_ts = date_from if date_from is not None else end_ts - 30 * 86400
    return start_ts, end_ts


def _age_bucket(birth_year: int | None) -> str:
    if birth_year is None:
        return "Не указан"
    age = time.gmtime().tm_year - birth_year
    if 18 <= age <= 24:
        return "18-24"
    if 25 <= age <= 34:
        return "25-34"
    if 35 <= age <= 44:
        return "35-44"
    if 45 <= age <= 54:
        return "45-54"
    if age >= 55:
        return "55+"
    return "Не указан"


@router.get("/customers", response_model=CustomersAnalyticsResponse)
def customers_analytics(
    created_from: int | None = Query(default=None),
    created_to: int | None = Query(default=None),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CustomersAnalyticsResponse:
    start_ts, end_ts = _range_bounds(created_from, created_to)

    total_clients = db.execute(
        select(func.count()).where(Client.salon_id == ctx.salon_id)
    ).scalar_one()

    buyers_q = (
        select(func.count(func.distinct(Operation.client_id)))
        .where(
            and_(
                Operation.salon_id == ctx.salon_id,
                Operation.op_type == "purchase",
                Operation.created_at >= start_ts,
                Operation.created_at <= end_ts,
            )
        )
    )
    buyers_count = int(db.execute(buyers_q).scalar_one() or 0)

    digitized_clients = int(
        db.execute(
            select(func.count()).where(and_(Client.salon_id == ctx.salon_id, Client.tg_id.is_not(None)))
        ).scalar_one()
        or 0
    )

    turnover = int(
        db.execute(
            select(func.coalesce(func.sum(Operation.amount_rub), 0)).where(
                and_(
                    Operation.salon_id == ctx.salon_id,
                    Operation.created_at >= start_ts,
                    Operation.created_at <= end_ts,
                )
            )
        ).scalar_one()
        or 0
    )
    income = int(
        db.execute(
            select(
                func.coalesce(
                    func.sum(Operation.amount_rub - Operation.discount_rub - Operation.referral_discount_rub), 0
                )
            ).where(
                and_(
                    Operation.salon_id == ctx.salon_id,
                    Operation.created_at >= start_ts,
                    Operation.created_at <= end_ts,
                )
            )
        ).scalar_one()
        or 0
    )
    discount = int(
        db.execute(
            select(func.coalesce(func.sum(Operation.discount_rub + Operation.referral_discount_rub), 0)).where(
                and_(
                    Operation.salon_id == ctx.salon_id,
                    Operation.created_at >= start_ts,
                    Operation.created_at <= end_ts,
                )
            )
        ).scalar_one()
        or 0
    )

    purchases_count = int(
        db.execute(
            select(func.count()).where(
                and_(
                    Operation.salon_id == ctx.salon_id,
                    Operation.op_type == "purchase",
                    Operation.created_at >= start_ts,
                    Operation.created_at <= end_ts,
                )
            )
        ).scalar_one()
        or 0
    )
    avg_check = round(turnover / purchases_count, 2) if purchases_count else 0

    balance_points = int(
        db.execute(
            select(func.coalesce(func.sum(Client.total_spent_rub / 100), 0)).where(Client.salon_id == ctx.salon_id)
        ).scalar_one()
        or 0
    )
    repeat_purchases = int(
        db.execute(
            select(func.count())
            .select_from(select(Client.id).where(and_(Client.salon_id == ctx.salon_id, Client.visits_count >= 2)).subquery())
        ).scalar_one()
        or 0
    )
    refunds = int(
        db.execute(
            select(func.count()).where(
                and_(
                    Operation.salon_id == ctx.salon_id,
                    Operation.op_type == "refund",
                    Operation.created_at >= start_ts,
                    Operation.created_at <= end_ts,
                )
            )
        ).scalar_one()
        or 0
    )
    avg_income = round(income / buyers_count, 2) if buyers_count else 0

    analytics_rows = db.execute(
        select(ClientAnalytics).where(
            and_(
                ClientAnalytics.salon_id == ctx.salon_id,
                ClientAnalytics.created_at >= start_ts,
                ClientAnalytics.created_at <= end_ts,
            )
        )
    ).scalars().all()

    gender_map = {"male": 0, "female": 0, "unknown": 0}
    age_map = {"18-24": 0, "25-34": 0, "35-44": 0, "45-54": 0, "55+": 0, "Не указан": 0}
    daily_new: dict[int, int] = {}

    for row in analytics_rows:
        gender_map[row.gender if row.gender in gender_map else "unknown"] += 1
        age_map[_age_bucket(row.birth_year)] += 1
        day = row.created_at - (row.created_at % 86400)
        daily_new[day] = daily_new.get(day, 0) + 1

    cards = [
        MetricCard(code="total_clients", title="Всего клиентов", value=int(total_clients)),
        MetricCard(code="buyers", title="Покупателей", value=buyers_count),
        MetricCard(code="digitized", title="Оцифрованных клиентов", value=digitized_clients),
        MetricCard(code="avg_check", title="Средний чек", value=avg_check),
        MetricCard(code="turnover", title="Оборот", value=turnover),
        MetricCard(code="income", title="Доход", value=income),
        MetricCard(code="discount", title="Скидка", value=discount),
        MetricCard(code="points", title="Баллов у клиентов", value=balance_points),
        MetricCard(code="purchases_count", title="Количество покупок", value=purchases_count),
        MetricCard(code="repeat_purchases", title="Повторные покупки", value=repeat_purchases),
        MetricCard(code="refunds", title="Возвраты", value=refunds),
        MetricCard(code="avg_income", title="Средний доход", value=avg_income),
    ]

    gender_distribution = [
        DistributionItem(label="Мужчины", value=gender_map["male"]),
        DistributionItem(label="Женщины", value=gender_map["female"]),
        DistributionItem(label="Не указан", value=gender_map["unknown"]),
    ]
    age_distribution = [DistributionItem(label=k, value=v) for k, v in age_map.items()]
    new_clients_series = [SeriesPoint(ts=k, value=v) for k, v in sorted(daily_new.items())]

    return CustomersAnalyticsResponse(
        cards=cards,
        gender_distribution=gender_distribution,
        age_distribution=age_distribution,
        new_clients_series=new_clients_series,
    )


@router.get("/operations", response_model=OperationsAnalyticsResponse)
def operations_analytics(
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> OperationsAnalyticsResponse:
    start_ts, end_ts = _range_bounds(date_from, date_to)
    rows = db.execute(
        select(Operation).where(
            and_(
                Operation.salon_id == ctx.salon_id,
                Operation.created_at >= start_ts,
                Operation.created_at <= end_ts,
            )
        )
    ).scalars().all()

    turnover = sum(x.amount_rub for x in rows)
    income = sum(max(x.amount_rub - x.discount_rub - x.referral_discount_rub, 0) for x in rows)
    discount = sum(x.discount_rub + x.referral_discount_rub for x in rows)
    purchases = [x for x in rows if x.op_type == "purchase"]
    orders = [x for x in rows if x.op_type == "order"]
    refunds = [x for x in rows if x.op_type == "refund"]
    avg_check = round(turnover / len(purchases), 2) if purchases else 0

    daily_counts: dict[int, int] = {}
    for row in rows:
        day = row.created_at - (row.created_at % 86400)
        daily_counts[day] = daily_counts.get(day, 0) + 1

    cards = [
        MetricCard(code="turnover", title="Оборот", value=turnover),
        MetricCard(code="income", title="Доход", value=income),
        MetricCard(code="discount", title="Скидка", value=discount),
        MetricCard(code="avg_check", title="Средний чек", value=avg_check),
        MetricCard(code="operations_purchase", title="Операций покупок", value=len(purchases)),
        MetricCard(code="cash_purchases", title="Покупки на кассе", value=len(purchases)),
        MetricCard(code="orders", title="Заказы", value=len(orders)),
        MetricCard(code="refunds", title="Возвраты", value=len(refunds)),
    ]

    return OperationsAnalyticsResponse(
        cards=cards,
        operations_series=[SeriesPoint(ts=k, value=v) for k, v in sorted(daily_counts.items())],
    )


@router.get("/ratings", response_model=RatingAnalyticsResponse)
def ratings_analytics(
    mode: str = Query(default="payments", pattern="^(payments|recommendations)$"),
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> RatingAnalyticsResponse:
    start_ts, end_ts = _range_bounds(date_from, date_to)
    feedback_type = "rating" if mode == "payments" else "suggestion"

    rows = db.execute(
        select(Feedback).where(
            and_(
                Feedback.salon_id == ctx.salon_id,
                Feedback.feedback_type == feedback_type,
                Feedback.created_at >= start_ts,
                Feedback.created_at <= end_ts,
            )
        )
    ).scalars().all()

    distribution_map = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    rated = [x.rating for x in rows if x.rating is not None]
    for r in rated:
        distribution_map[str(r)] = distribution_map.get(str(r), 0) + 1

    average = round(sum(rated) / len(rated), 2) if rated else 0.0
    return RatingAnalyticsResponse(
        mode=mode,
        average_rating=average,
        total_reviews=len(rows),
        distribution=[DistributionItem(label=k, value=v) for k, v in distribution_map.items()],
    )


@router.get("/levels", response_model=LevelsAnalyticsResponse)
def levels_analytics(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> LevelsAnalyticsResponse:
    rows = db.execute(select(Client).where(Client.salon_id == ctx.salon_id)).scalars().all()

    levels = {
        "0-999": {"all": 0, "bought": 0},
        "1000-4999": {"all": 0, "bought": 0},
        "5000+": {"all": 0, "bought": 0},
    }

    for row in rows:
        spent = row.total_spent_rub
        if spent < 1000:
            key = "0-999"
        elif spent < 5000:
            key = "1000-4999"
        else:
            key = "5000+"
        levels[key]["all"] += 1
        if row.visits_count > 0:
            levels[key]["bought"] += 1

    items = [
        LevelsAnalyticsItem(
            level=key,
            clients_total=value["all"],
            bought_clients=value["bought"],
            not_bought_clients=value["all"] - value["bought"],
        )
        for key, value in levels.items()
    ]
    return LevelsAnalyticsResponse(items=items)


@router.get("/page-go", response_model=AppVisitsAnalyticsResponse)
def page_go_analytics(
    mode: str = Query(default="views", pattern="^(views|visitors)$"),
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    detailing: str = Query(default="day", pattern="^(day|week|month)$"),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> AppVisitsAnalyticsResponse:
    start_ts, end_ts = _range_bounds(date_from, date_to)
    rows = db.execute(
        select(AppPageEvent).where(
            and_(
                AppPageEvent.salon_id == ctx.salon_id,
                AppPageEvent.created_at >= start_ts,
                AppPageEvent.created_at <= end_ts,
            )
        )
    ).scalars().all()

    bucket_seconds = {"day": 86400, "week": 7 * 86400, "month": 30 * 86400}[detailing]
    bucket: dict[int, int] = {}
    visitors_set: dict[int, set[str]] = {}

    for row in rows:
        ts = row.created_at - (row.created_at % bucket_seconds)
        if mode == "views":
            bucket[ts] = bucket.get(ts, 0) + 1
        else:
            visitors_set.setdefault(ts, set()).add(row.visitor_key or f"client:{row.client_id or 0}")

    if mode == "visitors":
        for ts, values in visitors_set.items():
            bucket[ts] = len(values)

    info_text = (
        "Просмотры — общее количество просмотров страницы компании в UDS app."
        if mode == "views"
        else "Посетители — уникальные пользователи страницы компании в UDS app по дням."
    )

    return AppVisitsAnalyticsResponse(
        mode=mode,
        detailing=detailing,
        timezone="GMT+03:00",
        info_text=info_text,
        series=[SeriesPoint(ts=k, value=v) for k, v in sorted(bucket.items())],
    )
