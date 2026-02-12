from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import (
    AppPageEvent,
    Client,
    ClientAnalytics,
    CommunicationCampaign,
    CommunicationRecipient,
    Feedback,
    Operation,
    ReferralProgramGenerationRule,
    ReferralProgramSetting,
    TrafficChannel,
)
from app.schemas.analytics import (
    AppVisitsAnalyticsResponse,
    CustomersAnalyticsResponse,
    DistributionItem,
    LevelsAnalyticsItem,
    LevelsAnalyticsResponse,
    MarketingAnalyticsResponse,
    MarketingAutomationStats,
    MarketingChannelStats,
    MarketingForecastPoint,
    MarketingFunnelStage,
    MarketingSegment,
    MetricCard,
    OperationsAnalyticsResponse,
    PromotionForecastGeneration,
    PromotionForecastRequest,
    PromotionForecastResponse,
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


def _percent(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 0.0


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
