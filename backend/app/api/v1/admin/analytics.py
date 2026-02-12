from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import (
    AppPageEvent,
    Appointment,
    Client,
    ClientAnalytics,
    CommunicationCampaign,
    CommunicationRecipient,
    ControlTowerPolicy,
    ControlTowerProfile,
    Feedback,
    Operation,
    OutcomeCatalogItem,
    ProcessKPIConfig,
    Product,
    ReferralProgramGenerationRule,
    ReferralProgramSetting,
    StockBalance,
    TrafficChannel,
)
from app.schemas.analytics import (
    AppVisitsAnalyticsResponse,
    ControlTowerActionItem,
    ControlTowerAnalyticsResponse,
    ControlTowerBookingStats,
    ControlTowerInventoryStats,
    ControlTowerPolicyResponse,
    ControlTowerPolicyUpdateRequest,
    ControlTowerSalesFunnelStage,
    CustomersAnalyticsResponse,
    DistributionItem,
    EndpointSpecItem,
    FinanceAnalyticsResponse,
    FinanceCategoryBreakdownItem,
    LevelsAnalyticsItem,
    LevelsAnalyticsResponse,
    MarketingAnalyticsResponse,
    MarketingAutomationStats,
    MarketingChannelStats,
    MarketingForecastPoint,
    MarketingFunnelStage,
    MarketingSegment,
    MetricCard,
    OnboardingGoalRequest,
    OnboardingGoalResponse,
    OperationsAnalyticsResponse,
    OutcomeCatalogItemResponse,
    ProcessKPIItem,
    ProcessKPIUpdateRequest,
    PromotionForecastGeneration,
    PromotionForecastRequest,
    PromotionForecastResponse,
    RatingAnalyticsResponse,
    SeriesPoint,
    VerticalPresetResponse,
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


def _percent(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 0.0


def _split_steps(raw: str) -> list[str]:
    return [step.strip() for step in raw.split(";") if step.strip()]


def _serialize_policy(policy: ControlTowerPolicy) -> ControlTowerPolicyResponse:
    return ControlTowerPolicyResponse(
        max_touches_per_week=policy.max_touches_per_week,
        min_hours_between_touches=policy.min_hours_between_touches,
        channel_priority=[x.strip() for x in policy.channel_priority_csv.split(",") if x.strip()],
        min_phone_fill_percent=policy.min_phone_fill_percent,
        min_consent_fill_percent=policy.min_consent_fill_percent,
        enforce_quiet_hours=policy.enforce_quiet_hours,
        quiet_hours_start=policy.quiet_hours_start,
        quiet_hours_end=policy.quiet_hours_end,
    )


def _vertical_presets() -> dict[str, VerticalPresetResponse]:
    return {
        "salon": VerticalPresetResponse(
            vertical="salon",
            title="Салон красоты",
            default_goal_90d="Снизить no-show до 12% и увеличить repeat до 35%",
            kpi_defaults=[
                MetricCard(code="no_show", title="No-show", value=12),
                MetricCard(code="conversion", title="Конверсия в покупку", value=60),
                MetricCard(code="repeat", title="Repeat", value=35),
            ],
            process_codes=["booking_confirmation", "visit_conversion", "sales_conversion", "repeat_sales"],
        ),
        "clinic": VerticalPresetResponse(
            vertical="clinic",
            title="Клиника",
            default_goal_90d="Повысить доходимость пациентов и загрузку расписания",
            kpi_defaults=[
                MetricCard(code="appointment_fill", title="Заполненность расписания", value=80),
                MetricCard(code="no_show", title="No-show", value=8),
                MetricCard(code="repeat", title="Повторные визиты", value=45),
            ],
            process_codes=["lead_capture", "booking_confirmation", "visit_conversion", "repeat_sales"],
        ),
        "retail": VerticalPresetResponse(
            vertical="retail",
            title="Магазин",
            default_goal_90d="Увеличить средний чек и удержать OOS ниже 4%",
            kpi_defaults=[
                MetricCard(code="avg_check", title="Средний чек", value=2400),
                MetricCard(code="oos", title="Out-of-stock", value=4),
                MetricCard(code="romi", title="ROMI", value=150),
            ],
            process_codes=["sales_conversion", "inventory_health", "campaign_roi", "repeat_sales"],
        ),
        "fitness": VerticalPresetResponse(
            vertical="fitness",
            title="Фитнес-центр",
            default_goal_90d="Поднять продление абонементов и снизить отток",
            kpi_defaults=[
                MetricCard(code="renewal", title="Продление абонементов", value=65),
                MetricCard(code="attendance", title="Посещаемость", value=75),
                MetricCard(code="repeat", title="Повторные покупки", value=40),
            ],
            process_codes=["booking_confirmation", "visit_conversion", "repeat_sales", "campaign_roi"],
        ),
    }


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


@router.get("/finance", response_model=FinanceAnalyticsResponse)
def finance_analytics(
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    detailing: str = Query(default="day", pattern="^(day|week|month)$"),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> FinanceAnalyticsResponse:
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

    incomes = [row for row in rows if row.op_type in {"purchase", "order"}]
    refunds = [row for row in rows if row.op_type == "refund"]

    purchase_income = sum(row.amount_rub for row in incomes if row.op_type == "purchase")
    order_income = sum(row.amount_rub for row in incomes if row.op_type == "order")
    income_total = purchase_income + order_income
    discount_total = sum(row.discount_rub + row.referral_discount_rub for row in rows)
    refund_total = sum(row.amount_rub for row in refunds)
    net_income = income_total - discount_total - refund_total

    bucket_seconds = {"day": 86400, "week": 7 * 86400, "month": 30 * 86400}[detailing]
    bucket_map: dict[int, int] = {}
    for row in rows:
        ts = row.created_at - (row.created_at % bucket_seconds)
        signed_amount = row.amount_rub if row.op_type in {"purchase", "order"} else -row.amount_rub
        bucket_map[ts] = bucket_map.get(ts, 0) + signed_amount

    total_income_for_share = income_total or 1
    total_expenses = discount_total + refund_total
    total_expenses_for_share = total_expenses or 1

    income_by_source = [
        FinanceCategoryBreakdownItem(
            code="purchases",
            title="Покупки",
            amount_rub=purchase_income,
            share_percent=round((purchase_income / total_income_for_share) * 100, 2),
        ),
        FinanceCategoryBreakdownItem(
            code="orders",
            title="Заказы",
            amount_rub=order_income,
            share_percent=round((order_income / total_income_for_share) * 100, 2),
        ),
    ]

    expenses_by_source = [
        FinanceCategoryBreakdownItem(
            code="discounts",
            title="Скидки",
            amount_rub=discount_total,
            share_percent=round((discount_total / total_expenses_for_share) * 100, 2),
        ),
        FinanceCategoryBreakdownItem(
            code="refunds",
            title="Возвраты",
            amount_rub=refund_total,
            share_percent=round((refund_total / total_expenses_for_share) * 100, 2),
        ),
    ]

    cards = [
        MetricCard(code="income_total", title="Доходы", value=income_total),
        MetricCard(code="discount_total", title="Скидки", value=discount_total),
        MetricCard(code="refund_total", title="Возвраты", value=refund_total),
        MetricCard(code="net_income", title="Чистый доход", value=net_income),
        MetricCard(code="operations_count", title="Операций", value=len(rows)),
        MetricCard(
            code="avg_income_per_operation",
            title="Средний доход на операцию",
            value=round(net_income / len(rows), 2) if rows else 0,
        ),
    ]

    return FinanceAnalyticsResponse(
        cards=cards,
        cashflow_series=[SeriesPoint(ts=k, value=v) for k, v in sorted(bucket_map.items())],
        income_by_source=income_by_source,
        expenses_by_source=expenses_by_source,
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


@router.get("/marketing", response_model=MarketingAnalyticsResponse)
def marketing_analytics(
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> MarketingAnalyticsResponse:
    start_ts, end_ts = _range_bounds(date_from, date_to)

    clients = db.execute(
        select(Client).where(Client.salon_id == ctx.salon_id)
    ).scalars().all()
    operations = db.execute(
        select(Operation).where(
            and_(
                Operation.salon_id == ctx.salon_id,
                Operation.created_at >= start_ts,
                Operation.created_at <= end_ts,
            )
        )
    ).scalars().all()
    channels = db.execute(
        select(TrafficChannel).where(TrafficChannel.salon_id == ctx.salon_id)
    ).scalars().all()

    clients_by_id = {row.id: row for row in clients}
    channels_by_id = {row.id: row for row in channels}

    purchases = [row for row in operations if row.op_type == "purchase"]
    buyers_ids = {row.client_id for row in purchases}
    new_clients = [row for row in clients if start_ts <= (row.last_visit_at or 0) <= end_ts]
    retained_clients = [row for row in clients if row.visits_count >= 2]

    card_total_clients = len(clients)
    card_buyers = len(buyers_ids)
    card_conversion = _percent(card_buyers, card_total_clients)
    card_revenue = int(sum(row.amount_rub for row in purchases))
    card_avg_check = round(card_revenue / len(purchases), 2) if purchases else 0.0

    channel_stats: list[MarketingChannelStats] = []
    channel_client_map: dict[int | None, list[Client]] = {None: []}
    for row in channels:
        channel_client_map[row.id] = []

    for client in clients:
        channel_client_map.setdefault(client.acquisition_channel_id, []).append(client)

    purchases_by_channel: dict[int | None, list[Operation]] = {key: [] for key in channel_client_map.keys()}
    for row in purchases:
        client = clients_by_id.get(row.client_id)
        channel_id = client.acquisition_channel_id if client is not None else None
        purchases_by_channel.setdefault(channel_id, []).append(row)

    for channel_id, channel_clients in channel_client_map.items():
        channel_purchases = purchases_by_channel.get(channel_id, [])
        channel_buyers = {row.client_id for row in channel_purchases}
        channel_name = channels_by_id[channel_id].name if channel_id in channels_by_id else "Без источника"
        channel_stats.append(
            MarketingChannelStats(
                channel_id=channel_id,
                channel_name=channel_name,
                clients_total=len(channel_clients),
                buyers_total=len(channel_buyers),
                purchases_total=len(channel_purchases),
                revenue_rub=int(sum(row.amount_rub for row in channel_purchases)),
                conversion_to_purchase_percent=_percent(len(channel_buyers), len(channel_clients)),
            )
        )

    channel_stats.sort(key=lambda row: row.revenue_rub, reverse=True)

    funnel_stages = [
        MarketingFunnelStage(
            code="lead",
            title="Лиды (все клиенты)",
            clients=card_total_clients,
            conversion_percent=100.0 if card_total_clients else 0.0,
        ),
        MarketingFunnelStage(
            code="engaged",
            title="Вовлечённые (минимум 1 визит)",
            clients=len([row for row in clients if row.visits_count > 0]),
            conversion_percent=_percent(len([row for row in clients if row.visits_count > 0]), card_total_clients),
        ),
        MarketingFunnelStage(
            code="buyers",
            title="Покупатели",
            clients=card_buyers,
            conversion_percent=card_conversion,
        ),
        MarketingFunnelStage(
            code="retained",
            title="Повторные покупки (retention)",
            clients=len(retained_clients),
            conversion_percent=_percent(len(retained_clients), card_total_clients),
        ),
    ]

    segmentation_map: dict[str, list[Client]] = {
        "Согласие на маркетинг": [row for row in clients if row.consent_marketing],
        "Без согласия на маркетинг": [row for row in clients if not row.consent_marketing],
        "Есть Telegram": [row for row in clients if row.tg_id is not None],
        "Нет Telegram": [row for row in clients if row.tg_id is None],
    }

    segments: list[MarketingSegment] = []
    for name, group_clients in segmentation_map.items():
        group_ids = {row.id for row in group_clients}
        buyers_in_group = len(group_ids & buyers_ids)
        segments.append(
            MarketingSegment(
                segment=name,
                clients_total=len(group_clients),
                buyers_total=buyers_in_group,
                conversion_percent=_percent(buyers_in_group, len(group_clients)),
            )
        )

    campaign_ids = db.execute(
        select(CommunicationCampaign.id).where(
            and_(
                CommunicationCampaign.salon_id == ctx.salon_id,
                CommunicationCampaign.created_at >= start_ts,
                CommunicationCampaign.created_at <= end_ts,
            )
        )
    ).scalars().all()

    recipient_rows: list[CommunicationRecipient] = []
    if campaign_ids:
        recipient_rows = db.execute(
            select(CommunicationRecipient).where(CommunicationRecipient.campaign_id.in_(campaign_ids))
        ).scalars().all()

    sent_total = len([row for row in recipient_rows if row.sent_at is not None])
    opened_total = len([row for row in recipient_rows if row.opened_at is not None])
    clicked_total = len([row for row in recipient_rows if row.clicked_at is not None])
    converted_total = len([row for row in recipient_rows if row.converted_at is not None])

    automation = MarketingAutomationStats(
        campaigns_total=len(campaign_ids),
        sent_total=sent_total,
        opened_total=opened_total,
        clicked_total=clicked_total,
        converted_total=converted_total,
        open_rate_percent=_percent(opened_total, sent_total),
        click_rate_percent=_percent(clicked_total, sent_total),
        conversion_rate_percent=_percent(converted_total, sent_total),
    )

    forecast_start = max(0, start_ts - (end_ts - start_ts))
    prev_new_clients = len([row for row in clients if forecast_start <= (row.last_visit_at or 0) < start_ts])
    current_new_clients = len(new_clients)
    trend = current_new_clients - prev_new_clients

    forecast: list[MarketingForecastPoint] = []
    period_seconds = max(1, end_ts - start_ts)
    for idx in range(1, 5):
        point_ts = end_ts + idx * period_seconds
        forecast.append(
            MarketingForecastPoint(
                ts=point_ts,
                new_clients_actual=current_new_clients,
                new_clients_forecast=max(0, current_new_clients + trend * idx),
            )
        )

    top_channel = channel_stats[0].channel_name if channel_stats else "—"
    insights = [
        f"Сквозная аналитика: лидирующий источник по выручке — {top_channel}.",
        f"Конверсия в покупку: {card_conversion}% ({card_buyers} из {card_total_clients} клиентов).",
        f"CRM-маркетинг: open rate {automation.open_rate_percent}%, click rate {automation.click_rate_percent}%.",
        f"Удержание: доля клиентов с повторными покупками — {_percent(len(retained_clients), card_total_clients)}%.",
        "Прогноз: используйте динамику новых клиентов для перераспределения бюджета в эффективные каналы.",
    ]

    return MarketingAnalyticsResponse(
        cards=[
            MetricCard(code="clients_total", title="Клиенты", value=card_total_clients),
            MetricCard(code="buyers_total", title="Покупатели", value=card_buyers),
            MetricCard(code="conversion_to_purchase", title="Конверсия в покупку, %", value=card_conversion),
            MetricCard(code="revenue", title="Выручка, ₽", value=card_revenue),
            MetricCard(code="avg_check", title="Средний чек, ₽", value=card_avg_check),
        ],
        channels=channel_stats,
        funnel=funnel_stages,
        segments=segments,
        automation=automation,
        forecast=forecast,
        insights=insights,
    )


@router.post("/promotion-forecast", response_model=PromotionForecastResponse)
def promotion_forecast(
    req: PromotionForecastRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> PromotionForecastResponse:
    setting = db.execute(
        select(ReferralProgramSetting).where(ReferralProgramSetting.salon_id == ctx.salon_id)
    ).scalar_one_or_none()

    generation_rows: list[ReferralProgramGenerationRule] = []
    reward_unit = "points"
    max_generations = 1
    if setting is not None and setting.is_active:
        generation_rows = db.execute(
            select(ReferralProgramGenerationRule)
            .where(ReferralProgramGenerationRule.setting_id == setting.id)
            .order_by(ReferralProgramGenerationRule.generation.asc())
        ).scalars().all()
        reward_unit = setting.reward_unit
        max_generations = setting.max_generations

    generation_rows = [x for x in generation_rows if x.is_enabled and x.generation <= max_generations]

    conversion = req.conversion_rate_percent / 100
    margin = req.gross_margin_percent / 100

    generations: list[PromotionForecastGeneration] = []
    total_new_clients = 0
    reward_cost = 0.0

    current_base = req.initial_clients * conversion
    base_reward = req.avg_check_rub if reward_unit == "money" else req.avg_check_rub * 0.3

    for row in generation_rows:
        expected_clients = int(round(current_base))
        level_cost = expected_clients * base_reward * (row.reward_percent / 100)

        total_new_clients += expected_clients
        reward_cost += level_cost
        generations.append(
            PromotionForecastGeneration(
                generation=row.generation,
                expected_new_clients=expected_clients,
                expected_reward_cost_rub=round(level_cost, 2),
            )
        )
        current_base = expected_clients * conversion

    projected_revenue = round(total_new_clients * req.avg_check_rub, 2)
    projected_gross_profit = round(projected_revenue * margin, 2)
    projected_net_effect = round(projected_gross_profit - reward_cost, 2)

    per_client_profit = req.avg_check_rub * margin
    per_client_reward = (reward_cost / total_new_clients) if total_new_clients else 0
    per_client_net = per_client_profit - per_client_reward

    if per_client_net <= 0:
        break_even_new_clients = 0
        break_even_conversion_rate = 0.0
    else:
        break_even_new_clients = int(round(reward_cost / per_client_profit)) if per_client_profit else 0
        break_even_conversion_rate = round((break_even_new_clients / max(req.initial_clients, 1)) * 100, 2)

    return PromotionForecastResponse(
        period_days=req.period_days,
        projected_clients_total=total_new_clients,
        projected_revenue_rub=projected_revenue,
        projected_gross_profit_rub=projected_gross_profit,
        projected_reward_cost_rub=round(reward_cost, 2),
        projected_net_effect_rub=projected_net_effect,
        break_even_new_clients=break_even_new_clients,
        break_even_conversion_rate_percent=break_even_conversion_rate,
        generations=generations,
    )


@router.get("/control-tower", response_model=ControlTowerAnalyticsResponse)
def control_tower_analytics(
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ControlTowerAnalyticsResponse:
    start_ts, end_ts = _range_bounds(date_from, date_to)
    now_ts = int(time.time())

    clients = db.execute(select(Client).where(Client.salon_id == ctx.salon_id)).scalars().all()
    operations = db.execute(
        select(Operation).where(
            and_(
                Operation.salon_id == ctx.salon_id,
                Operation.created_at >= start_ts,
                Operation.created_at <= end_ts,
            )
        )
    ).scalars().all()
    appointments = db.execute(
        select(Appointment).where(
            and_(
                Appointment.salon_id == ctx.salon_id,
                Appointment.starts_at >= start_ts,
                Appointment.starts_at <= end_ts,
            )
        )
    ).scalars().all()

    stock_rows = db.execute(
        select(Product, StockBalance).join(
            StockBalance,
            and_(
                StockBalance.product_id == Product.id,
                StockBalance.salon_id == Product.salon_id,
            ),
        )
        .where(Product.salon_id == ctx.salon_id)
    ).all()

    purchases = [row for row in operations if row.op_type == "purchase"]
    buyers_ids = {row.client_id for row in purchases}
    conversion_purchase = _percent(len(buyers_ids), len(clients))

    revenue_total = int(sum(row.amount_rub for row in purchases))
    avg_check = round(revenue_total / len(purchases), 2) if purchases else 0

    appointments_total = len(appointments)
    appointments_completed = len([row for row in appointments if row.status == "completed"])
    appointments_cancelled = len([row for row in appointments if row.status == "cancelled"])
    no_show_risk = _percent(appointments_cancelled, appointments_total)

    future_bookings = [row for row in appointments if row.starts_at > now_ts and row.status == "scheduled"]
    future_bookings_total = len(future_bookings)
    future_revenue_forecast = int(round(future_bookings_total * avg_check))

    sku_totals: dict[int, dict[str, int | str]] = {}
    for product, stock in stock_rows:
        item = sku_totals.setdefault(
            product.id,
            {"name": product.name, "quantity": 0, "price_rub": int(product.price_rub)},
        )
        item["quantity"] = int(item["quantity"]) + int(stock.quantity)

    inventory_valuation = sum(int(item["quantity"]) * int(item["price_rub"]) for item in sku_totals.values())
    low_stock_positions = len([item for item in sku_totals.values() if 0 < int(item["quantity"]) <= 5])
    out_of_stock_positions = len([item for item in sku_totals.values() if int(item["quantity"]) <= 0])

    top_stock_items = sorted(sku_totals.values(), key=lambda item: int(item["quantity"]), reverse=True)[:5]

    repeat_clients = len([row for row in clients if row.visits_count >= 2])
    clients_with_visit = len([row for row in clients if row.visits_count > 0])

    cards = [
        MetricCard(code="revenue_total", title="Выручка", value=revenue_total),
        MetricCard(code="avg_check", title="Средний чек", value=avg_check),
        MetricCard(code="clients_total", title="Клиенты в базе", value=len(clients)),
        MetricCard(code="conversion_purchase", title="Конверсия в покупку", value=conversion_purchase),
        MetricCard(code="future_bookings_revenue", title="План выручки по записям", value=future_revenue_forecast),
        MetricCard(code="inventory_valuation", title="Оценка склада", value=inventory_valuation),
    ]

    sales_funnel = [
        ControlTowerSalesFunnelStage(
            code="clients",
            title="Клиенты в базе",
            clients=len(clients),
            conversion_percent=100.0 if clients else 0.0,
        ),
        ControlTowerSalesFunnelStage(
            code="engaged",
            title="С визитом",
            clients=clients_with_visit,
            conversion_percent=_percent(clients_with_visit, len(clients)),
        ),
        ControlTowerSalesFunnelStage(
            code="buyers",
            title="Покупатели",
            clients=len(buyers_ids),
            conversion_percent=conversion_purchase,
        ),
        ControlTowerSalesFunnelStage(
            code="repeat",
            title="Повторные",
            clients=repeat_clients,
            conversion_percent=_percent(repeat_clients, len(clients)),
        ),
    ]

    profile = db.execute(select(ControlTowerProfile).where(ControlTowerProfile.salon_id == ctx.salon_id)).scalar_one()
    policy = db.execute(select(ControlTowerPolicy).where(ControlTowerPolicy.salon_id == ctx.salon_id)).scalar_one()
    process_rows = db.execute(
        select(ProcessKPIConfig)
        .where(ProcessKPIConfig.salon_id == ctx.salon_id)
        .order_by(ProcessKPIConfig.priority_rank.asc())
    ).scalars().all()

    current_by_code = {
        "visit_conversion": no_show_risk,
        "booking_confirmation": _percent(appointments_completed + max(appointments_total - appointments_cancelled - appointments_completed, 0), max(appointments_total, 1)),
        "sales_conversion": conversion_purchase,
        "repeat_sales": _percent(repeat_clients, len(clients)),
        "inventory_health": _percent(out_of_stock_positions, max(len(sku_totals), 1)),
        "campaign_roi": 125.0,
        "lead_capture": _percent(clients_with_visit, len(clients)),
    }

    process_kpis: list[ProcessKPIItem] = []
    action_plan: list[ControlTowerActionItem] = []
    for row in process_rows:
        current_value = round(float(current_by_code.get(row.process_code, row.baseline_value)), 2)
        gap_to_target = round(float(row.target_value - current_value), 2)
        process_kpis.append(
            ProcessKPIItem(
                process_code=row.process_code,
                process_title=row.process_title,
                kpi_name=row.kpi_name,
                sla_name=row.sla_name,
                sla_target=row.sla_target,
                trigger_event=row.trigger_event,
                baseline_value=row.baseline_value,
                target_value=row.target_value,
                unit=row.unit,
                current_value=current_value,
                gap_to_target=gap_to_target,
                recommended_action=row.recommended_action,
                is_enabled=row.is_enabled,
                auto_orchestration_enabled=row.auto_orchestration_enabled,
            )
        )
        needs_attention = row.is_enabled and (
            (row.process_code == "visit_conversion" and current_value > row.target_value)
            or (row.process_code != "visit_conversion" and current_value < row.target_value)
        )
        if needs_attention:
            action_plan.append(
                ControlTowerActionItem(
                    code=f"action_{row.process_code}",
                    title=f"{row.process_title}: фокус на сегодня",
                    priority="high" if row.priority_rank <= 10 else "medium",
                    description=f"{row.kpi_name}: текущее {current_value}{'%' if row.unit == 'percent' else ''}, цель {row.target_value}{'%' if row.unit == 'percent' else ''}. {row.recommended_action}",
                )
            )

    if not action_plan:
        action_plan.append(
            ControlTowerActionItem(
                code="keep_growth",
                title="Поддерживать текущий рост",
                priority="low",
                description="Ключевые показатели в норме. Проверьте A/B тест акций для ускорения роста выручки.",
            )
        )

    return ControlTowerAnalyticsResponse(
        cards=cards,
        sales_funnel=sales_funnel,
        bookings=ControlTowerBookingStats(
            appointments_total=appointments_total,
            appointments_completed=appointments_completed,
            appointments_cancelled=appointments_cancelled,
            no_show_risk_percent=no_show_risk,
            future_bookings_total=future_bookings_total,
            future_bookings_revenue_forecast_rub=future_revenue_forecast,
        ),
        inventory=ControlTowerInventoryStats(
            sku_total=len(sku_totals),
            inventory_valuation_rub=int(inventory_valuation),
            low_stock_positions=low_stock_positions,
            out_of_stock_positions=out_of_stock_positions,
            top_stock_items=[
                MetricCard(
                    code=f"stock_item_{idx + 1}",
                    title=str(item["name"]),
                    value=int(item["quantity"]),
                )
                for idx, item in enumerate(top_stock_items)
            ],
        ),
        action_plan=action_plan,
        process_kpis=process_kpis,
        policy=_serialize_policy(policy),
        onboarding=OnboardingGoalResponse(
            vertical=profile.vertical,
            goal_90d=profile.goal_90d,
            dashboard_focus=profile.dashboard_focus,
            onboarding_completed=profile.onboarding_completed,
        ),
    )


@router.get("/control-tower/processes", response_model=list[ProcessKPIItem])
def control_tower_processes(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> list[ProcessKPIItem]:
    rows = db.execute(
        select(ProcessKPIConfig)
        .where(ProcessKPIConfig.salon_id == ctx.salon_id)
        .order_by(ProcessKPIConfig.priority_rank.asc())
    ).scalars().all()
    return [
        ProcessKPIItem(
            process_code=row.process_code,
            process_title=row.process_title,
            kpi_name=row.kpi_name,
            sla_name=row.sla_name,
            sla_target=row.sla_target,
            trigger_event=row.trigger_event,
            baseline_value=row.baseline_value,
            target_value=row.target_value,
            unit=row.unit,
            current_value=row.baseline_value,
            gap_to_target=round(row.target_value - row.baseline_value, 2),
            recommended_action=row.recommended_action,
            is_enabled=row.is_enabled,
            auto_orchestration_enabled=row.auto_orchestration_enabled,
        )
        for row in rows
    ]


@router.put("/control-tower/processes/{process_code}", response_model=ProcessKPIItem)
def update_control_tower_process(
    process_code: str,
    req: ProcessKPIUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ProcessKPIItem:
    row = db.execute(
        select(ProcessKPIConfig).where(
            and_(ProcessKPIConfig.salon_id == ctx.salon_id, ProcessKPIConfig.process_code == process_code)
        )
    ).scalar_one()
    if req.baseline_value is not None:
        row.baseline_value = req.baseline_value
    if req.target_value is not None:
        row.target_value = req.target_value
    if req.is_enabled is not None:
        row.is_enabled = req.is_enabled
    if req.auto_orchestration_enabled is not None:
        row.auto_orchestration_enabled = req.auto_orchestration_enabled
    db.commit()
    db.refresh(row)
    return ProcessKPIItem(
        process_code=row.process_code,
        process_title=row.process_title,
        kpi_name=row.kpi_name,
        sla_name=row.sla_name,
        sla_target=row.sla_target,
        trigger_event=row.trigger_event,
        baseline_value=row.baseline_value,
        target_value=row.target_value,
        unit=row.unit,
        current_value=row.baseline_value,
        gap_to_target=round(row.target_value - row.baseline_value, 2),
        recommended_action=row.recommended_action,
        is_enabled=row.is_enabled,
        auto_orchestration_enabled=row.auto_orchestration_enabled,
    )


@router.get("/control-tower/policy", response_model=ControlTowerPolicyResponse)
def control_tower_policy(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ControlTowerPolicyResponse:
    policy = db.execute(select(ControlTowerPolicy).where(ControlTowerPolicy.salon_id == ctx.salon_id)).scalar_one()
    return _serialize_policy(policy)


@router.put("/control-tower/policy", response_model=ControlTowerPolicyResponse)
def update_control_tower_policy(
    req: ControlTowerPolicyUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ControlTowerPolicyResponse:
    policy = db.execute(select(ControlTowerPolicy).where(ControlTowerPolicy.salon_id == ctx.salon_id)).scalar_one()
    if req.max_touches_per_week is not None:
        policy.max_touches_per_week = req.max_touches_per_week
    if req.min_hours_between_touches is not None:
        policy.min_hours_between_touches = req.min_hours_between_touches
    if req.channel_priority is not None:
        policy.channel_priority_csv = ",".join(req.channel_priority)
    if req.min_phone_fill_percent is not None:
        policy.min_phone_fill_percent = req.min_phone_fill_percent
    if req.min_consent_fill_percent is not None:
        policy.min_consent_fill_percent = req.min_consent_fill_percent
    if req.enforce_quiet_hours is not None:
        policy.enforce_quiet_hours = req.enforce_quiet_hours
    if req.quiet_hours_start is not None:
        policy.quiet_hours_start = req.quiet_hours_start
    if req.quiet_hours_end is not None:
        policy.quiet_hours_end = req.quiet_hours_end
    db.commit()
    db.refresh(policy)
    return _serialize_policy(policy)


@router.get("/control-tower/onboarding-goal", response_model=OnboardingGoalResponse)
def get_onboarding_goal(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> OnboardingGoalResponse:
    row = db.execute(select(ControlTowerProfile).where(ControlTowerProfile.salon_id == ctx.salon_id)).scalar_one()
    return OnboardingGoalResponse(
        vertical=row.vertical,
        goal_90d=row.goal_90d,
        dashboard_focus=row.dashboard_focus,
        onboarding_completed=row.onboarding_completed,
    )


@router.put("/control-tower/onboarding-goal", response_model=OnboardingGoalResponse)
def save_onboarding_goal(
    req: OnboardingGoalRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> OnboardingGoalResponse:
    row = db.execute(select(ControlTowerProfile).where(ControlTowerProfile.salon_id == ctx.salon_id)).scalar_one()
    row.vertical = req.vertical
    row.goal_90d = req.goal_90d
    row.dashboard_focus = req.dashboard_focus
    row.onboarding_completed = True
    db.commit()
    db.refresh(row)
    return OnboardingGoalResponse(
        vertical=row.vertical,
        goal_90d=row.goal_90d,
        dashboard_focus=row.dashboard_focus,
        onboarding_completed=row.onboarding_completed,
    )


@router.get("/control-tower/outcomes", response_model=list[OutcomeCatalogItemResponse])
def control_tower_outcomes(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> list[OutcomeCatalogItemResponse]:
    rows = db.execute(
        select(OutcomeCatalogItem).where(OutcomeCatalogItem.salon_id == ctx.salon_id).order_by(OutcomeCatalogItem.id.asc())
    ).scalars().all()
    return [
        OutcomeCatalogItemResponse(
            outcome_code=row.outcome_code,
            title=row.title,
            process_code=row.process_code,
            description=row.description,
            event_storming_steps=_split_steps(row.event_storming_steps),
        )
        for row in rows
    ]


@router.get("/control-tower/presets/{vertical}", response_model=VerticalPresetResponse)
def control_tower_vertical_presets(
    vertical: str,
    ctx=Depends(require_roles("owner", "admin")),
) -> VerticalPresetResponse:
    presets = _vertical_presets()
    return presets.get(vertical, presets["salon"])


@router.get("/control-tower/endpoint-specs", response_model=list[EndpointSpecItem])
def control_tower_endpoint_specs(
    ctx=Depends(require_roles("owner", "admin")),
) -> list[EndpointSpecItem]:
    return [
        EndpointSpecItem(
            endpoint="GET /api/v1/admin/analytics/control-tower",
            business_rules=[
                "1 экран = 1 решение: ответ включает только управленческие KPI и приоритетные действия.",
                "Action-план формируется из gap между current и target по эталонным процессам.",
            ],
            exceptions=[
                "При пустой базе возвращается безопасный план 'Поддерживать текущий рост'.",
                "Если политика частоты касаний нарушена, автооркестрация для процесса отключается.",
            ],
            data_examples=[
                {"process": "visit_conversion", "current": 18.0, "target": 10.0, "action": "Включить предоплату"},
                {"process": "inventory_health", "current": 11.0, "target": 4.0, "action": "Дозаказать SKU"},
            ],
        ),
        EndpointSpecItem(
            endpoint="PUT /api/v1/admin/analytics/control-tower/processes/{process_code}",
            business_rules=[
                "Для каждого улучшения обязательно хранится baseline и target.",
                "Процессы можно включать/выключать под конкретный бизнес.",
            ],
            exceptions=[
                "Если process_code не найден, возвращается 404.",
                "Нельзя установить отрицательные значения baseline/target.",
            ],
            data_examples=[
                {"process_code": "repeat_sales", "baseline_value": 21.0, "target_value": 33.0},
            ],
        ),
    ]
