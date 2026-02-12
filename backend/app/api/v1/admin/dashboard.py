from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Client, Operation, Salon, SystemSettings
from app.schemas.dashboard import (
    BuyersStats,
    DashboardAlert,
    DashboardFullResponse,
    DashboardPromoCard,
    DashboardSectionLink,
    DashboardSummaryResponse,
    FinanceStats,
    OperationsStats,
)

router = APIRouter(prefix="/admin/dashboard", tags=["admin.dashboard"])


def _get_summary(db: Session, salon_id: int) -> DashboardSummaryResponse:
    now = int(time.time())
    start_day = now - (now % 86400)

    finance_q = db.execute(
        select(
            func.coalesce(func.sum(Operation.amount_rub), 0),
            func.coalesce(func.sum(Operation.amount_rub - Operation.discount_rub - Operation.referral_discount_rub), 0),
            func.coalesce(func.sum(Operation.discount_rub + Operation.referral_discount_rub), 0),
        ).where(and_(Operation.salon_id == salon_id, Operation.created_at >= start_day))
    ).one()

    operations_q = db.execute(
        select(
            func.coalesce(func.sum(case((Operation.op_type == "purchase", 1), else_=0)), 0),
            func.coalesce(func.sum(case((Operation.op_type == "order", 1), else_=0)), 0),
            func.coalesce(func.sum(case((Operation.op_type == "refund", 1), else_=0)), 0),
        ).where(and_(Operation.salon_id == salon_id, Operation.created_at >= start_day))
    ).one()

    clients_total = db.execute(
        select(func.count()).select_from(select(Client.id).where(Client.salon_id == salon_id).subquery())
    ).scalar_one()
    buyers_new = db.execute(
        select(func.count()).select_from(
            select(Client.id)
            .where(and_(Client.salon_id == salon_id, Client.last_visit_at.is_not(None), Client.last_visit_at >= start_day))
            .subquery()
        )
    ).scalar_one()
    buyers_digitized = db.execute(
        select(func.count()).select_from(
            select(Client.id).where(and_(Client.salon_id == salon_id, Client.tg_id.is_not(None))).subquery()
        )
    ).scalar_one()

    return DashboardSummaryResponse(
        finance=FinanceStats(
            turnover_rub=int(finance_q[0] or 0),
            income_rub=int(finance_q[1] or 0),
            discount_rub=int(finance_q[2] or 0),
        ),
        buyers=BuyersStats(
            total=int(clients_total or 0),
            new=int(buyers_new or 0),
            digitized=int(buyers_digitized or 0),
        ),
        operations=OperationsStats(
            purchases_count=int(operations_q[0] or 0),
            orders_count=int(operations_q[1] or 0),
            refunds_count=int(operations_q[2] or 0),
        ),
        clients_count=int(clients_total or 0),
    )


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    return _get_summary(db, ctx.salon_id)


@router.get("/full", response_model=DashboardFullResponse)
def get_full_dashboard(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> DashboardFullResponse:
    summary = _get_summary(db, ctx.salon_id)
    salon = db.execute(select(Salon).where(Salon.id == ctx.salon_id)).scalar_one()
    settings = db.execute(
        select(SystemSettings).where(SystemSettings.salon_id == ctx.salon_id)
    ).scalar_one_or_none()

    alerts: list[DashboardAlert] = []
    if salon.subscription_ends_at is None or salon.subscription_ends_at - int(time.time()) < 7 * 86400:
        alerts.append(
            DashboardAlert(
                code="subscription",
                level="warning",
                title="Подписка заканчивается",
                subtitle="Выберите тариф",
                action_label="Выбрать тариф",
                action_route="/admin/billing",
            )
        )

    if salon.moderation_status != "approved":
        alerts.append(
            DashboardAlert(
                code="moderation",
                level="danger",
                title="На модерации",
                subtitle="Компания не прошла модерацию, проверьте замечания",
                action_label="Посмотреть замечания",
                action_route="/admin/moderation",
            )
        )

    avg_purchases = settings.avg_purchases_per_day if settings else 0
    promo_cards = [
        DashboardPromoCard(
            code="telegram_bonus_card",
            title="Бонусная карта ваших клиентов в Telegram",
            subtitle="Настройте бота за 5 минут",
            action_label="Настроить Telegram Bot",
            action_route="/admin/integrations/telegram",
        ),
        DashboardPromoCard(
            code="avg_purchases",
            title="Укажите среднее количество покупок на кассе в день",
            subtitle=f"Текущее значение: {avg_purchases}",
            action_label="Заполнить",
            action_route="/admin/options/system",
        ),
        DashboardPromoCard(
            code="manager",
            title="Подключите персонального менеджера",
            subtitle="Используйте на максимум все инструменты UDS",
            action_label="Подключить",
            action_route="/admin/support/manager",
        ),
        DashboardPromoCard(
            code="support",
            title="Служба поддержки",
            subtitle="Ответим на все ваши вопросы",
            action_label="Написать",
            action_route="/admin/support",
        ),
    ]

    section_links = [
        DashboardSectionLink(section="finance", route="/admin/statistics/finance"),
        DashboardSectionLink(section="buyers", route="/admin/customers"),
        DashboardSectionLink(section="operations", route="/admin/operations"),
        DashboardSectionLink(section="clients", route="/admin/customers"),
        DashboardSectionLink(
            section="promotion",
            route="/admin/promotion",
            children=[
                DashboardSectionLink(section="certificate_types", route="/admin/certificates/types"),
                DashboardSectionLink(section="certificates", route="/admin/certificates"),
                DashboardSectionLink(section="referral_programs", route="/admin/referral-programs/config"),
                DashboardSectionLink(section="promotion_forecast", route="/admin/analytics/promotion-forecast"),
            ],
        ),
    ]

    return DashboardFullResponse(
        summary=summary,
        section_links=section_links,
        alerts=alerts,
        promo_cards=promo_cards,
    )
