from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, inspect, select, text

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.web_admin import router as web_admin_router
from app.models import (
    ControlTowerPolicy,
    ControlTowerProfile,
    InventoryLocation,
    OutcomeCatalogItem,
    ProcessKPIConfig,
    ReferralProgramGenerationRule,
    ReferralProgramSetting,
    ReminderRule,
    Salon,
    SystemSettings,
    TrafficChannel,
)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)


def _ensure_column_sqlite(table: str, column_name: str, ddl: str) -> None:
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns(table)}
    if column_name in columns:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def _run_startup_schema_patches() -> None:
    # keep backward compatibility with pre-existing sqlite db files
    _ensure_column_sqlite("salons", "subscription_ends_at", "subscription_ends_at INTEGER")
    _ensure_column_sqlite(
        "salons",
        "moderation_status",
        "moderation_status VARCHAR(32) NOT NULL DEFAULT 'in_review'",
    )

    _ensure_column_sqlite("clients", "vk_username", "vk_username VARCHAR(128) NOT NULL DEFAULT ''")
    _ensure_column_sqlite("clients", "instagram_username", "instagram_username VARCHAR(128) NOT NULL DEFAULT ''")
    _ensure_column_sqlite("clients", "facebook_username", "facebook_username VARCHAR(128) NOT NULL DEFAULT ''")
    _ensure_column_sqlite("clients", "max_username", "max_username VARCHAR(128) NOT NULL DEFAULT ''")
    _ensure_column_sqlite("clients", "whatsapp_phone", "whatsapp_phone VARCHAR(32) NOT NULL DEFAULT ''")
    _ensure_column_sqlite("clients", "telegram_username", "telegram_username VARCHAR(128) NOT NULL DEFAULT ''")
    _ensure_column_sqlite("clients", "birthday", "birthday VARCHAR(10) NOT NULL DEFAULT ''")

    _ensure_column_sqlite("system_settings", "global_search_enabled", "global_search_enabled BOOLEAN NOT NULL DEFAULT 0")

    _ensure_column_sqlite("messages", "client_tg_id", "client_tg_id INTEGER")
    _ensure_column_sqlite("messages", "channel", "channel VARCHAR(24) NOT NULL DEFAULT 'telegram'")
    _ensure_column_sqlite("messages", "subject", "subject VARCHAR(200) NOT NULL DEFAULT ''")
    _ensure_column_sqlite("messages", "destination", "destination VARCHAR(255) NOT NULL DEFAULT ''")

    _ensure_column_sqlite("feedback", "object_type", "object_type VARCHAR(24) NOT NULL DEFAULT 'service'")
    _ensure_column_sqlite("feedback", "object_id", "object_id INTEGER")

    _ensure_column_sqlite("products", "item_type", "item_type VARCHAR(16) NOT NULL DEFAULT 'product'")
    _ensure_column_sqlite("products", "track_inventory", "track_inventory BOOLEAN NOT NULL DEFAULT 1")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.CORS_ALLOW_ORIGINS.split(",") if x.strip()] or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    _run_startup_schema_patches()
    with SessionLocal() as db:
        salon = db.execute(select(Salon).limit(1)).scalar_one_or_none()
        if salon is None:
            salon = Salon(
                name=settings.DEFAULT_SALON_NAME,
                moderation_status="in_review",
            )
            db.add(salon)
            db.flush()

        if salon.moderation_status is None:
            salon.moderation_status = "in_review"

        settings_row = db.execute(
            select(SystemSettings).where(SystemSettings.salon_id == salon.id)
        ).scalar_one_or_none()
        if settings_row is None:
            db.add(SystemSettings(salon_id=salon.id))

        reminder_count = db.execute(
            select(func.count()).where(ReminderRule.salon_id == salon.id)
        ).scalar_one()
        if not reminder_count:
            for offset in [60, 240, 1440, 10080]:
                db.add(ReminderRule(salon_id=salon.id, offset_minutes=offset, channel="app", is_enabled=True))

        location_count = db.execute(select(func.count()).where(InventoryLocation.salon_id == salon.id)).scalar_one()
        if not location_count:
            now = int(time.time())
            db.add(
                InventoryLocation(
                    salon_id=salon.id,
                    name="Основной склад",
                    location_type="warehouse",
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )


        referral_settings = db.execute(
            select(ReferralProgramSetting).where(ReferralProgramSetting.salon_id == salon.id)
        ).scalar_one_or_none()
        if referral_settings is None:
            referral_settings = ReferralProgramSetting(
                salon_id=salon.id,
                is_active=False,
                reward_unit="points",
                max_generations=3,
                base_reward_value=100,
            )
            db.add(referral_settings)
            db.flush()
            defaults = [10.0, 5.0, 3.0, 2.0, 1.0, 0.5]
            for idx, percent in enumerate(defaults, start=1):
                db.add(
                    ReferralProgramGenerationRule(
                        setting_id=referral_settings.id,
                        generation=idx,
                        reward_percent=percent,
                        is_enabled=idx <= 3,
                    )
                )

        defaults = [
            ("Web", "web", ""),
            ("UDS App", "uds_app", ""),
            ("Новые компании", "partner", ""),
            ("Размещения по CPA", "cpa", ""),
            ("Буферные клиенты", "buffer", ""),
        ]
        existing = {x.name for x in db.execute(select(TrafficChannel).where(TrafficChannel.salon_id == salon.id)).scalars().all()}
        now = int(time.time())
        for name, channel_type, promo_code in defaults:
            if name not in existing:
                db.add(
                    TrafficChannel(
                        salon_id=salon.id,
                        name=name,
                        channel_type=channel_type,
                        promo_code=promo_code,
                        created_at=now,
                    )
                )

        profile = db.execute(select(ControlTowerProfile).where(ControlTowerProfile.salon_id == salon.id)).scalar_one_or_none()
        if profile is None:
            db.add(
                ControlTowerProfile(
                    salon_id=salon.id,
                    vertical="salon",
                    goal_90d="Снизить no-show до 12% и увеличить выручку на 15%",
                    dashboard_focus="Выручка, запись и повторные продажи",
                    onboarding_completed=False,
                )
            )

        policy = db.execute(select(ControlTowerPolicy).where(ControlTowerPolicy.salon_id == salon.id)).scalar_one_or_none()
        if policy is None:
            db.add(ControlTowerPolicy(salon_id=salon.id))

        process_count = db.execute(select(func.count()).where(ProcessKPIConfig.salon_id == salon.id)).scalar_one()
        if not process_count:
            defaults = [
                ("lead_capture", "Привлечение лида", "Конверсия лида в запись", "SLA ответа на лид", 15, "new_client", 24, 35, "percent", "Подключить автоответ и оффер на первый визит.", 10),
                ("booking_confirmation", "Подтверждение записи", "Подтвержденные записи", "SLA подтверждения", 90, "appointment_created", 72, 92, "percent", "Автонапоминание за 24ч и 1ч + кнопка подтверждения.", 20),
                ("visit_conversion", "Запись в визит", "No-show", "SLA no-show", 12, "appointment_no_show", 18, 10, "percent", "Включить предоплату и сценарий дожима после пропуска.", 5),
                ("sales_conversion", "Визит в покупку", "Конверсия визит→покупка", "SLA конверсии", 55, "visit_completed", 42, 60, "percent", "Добавить персональные рекомендации и кросс-селл.", 15),
                ("repeat_sales", "Повторные продажи", "Repeat rate", "SLA повтора за 30 дней", 35, "purchase_completed", 21, 33, "percent", "Автоцепочка повторной покупки на 7/21 день.", 25),
                ("inventory_health", "Здоровье склада", "OOS доля", "SLA out-of-stock", 5, "stock_low", 11, 4, "percent", "Настроить минимальные остатки и триггер закупки.", 8),
                ("campaign_roi", "Эффективность кампаний", "ROMI", "SLA ROMI", 130, "campaign_sent", 105, 150, "percent", "Отключить нерентабельные каналы и усилить топ-2 сегмента.", 30),
            ]
            for code, title, kpi, sla, sla_target, trigger, baseline, target, unit, rec, prio in defaults:
                db.add(
                    ProcessKPIConfig(
                        salon_id=salon.id,
                        process_code=code,
                        process_title=title,
                        kpi_name=kpi,
                        sla_name=sla,
                        sla_target=float(sla_target),
                        trigger_event=trigger,
                        baseline_value=float(baseline),
                        target_value=float(target),
                        unit=unit,
                        recommended_action=rec,
                        is_enabled=True,
                        auto_orchestration_enabled=True,
                        priority_rank=prio,
                    )
                )

        outcomes_count = db.execute(select(func.count()).where(OutcomeCatalogItem.salon_id == salon.id)).scalar_one()
        if not outcomes_count:
            outcomes = [
                ("stable_schedule", "Стабильная запись", "booking_confirmation", "Стабилизировать загрузку расписания на 90 дней", "Лид→контакт; Контакт→запись; Запись→подтверждение; Подтверждение→визит"),
                ("higher_conversion", "Рост конверсии в покупку", "sales_conversion", "Увеличить долю визитов, завершившихся продажей", "Визит; Выявление потребности; Оффер; Оплата"),
                ("repeat_growth", "Рост повторных покупок", "repeat_sales", "Повысить retention и LTV", "Покупка; Follow-up; Повторный оффер; Повторная покупка"),
                ("low_no_show", "Снижение неявок", "visit_conversion", "Снизить no-show за счёт напоминаний и подтверждений", "Создание записи; Напоминание; Подтверждение; Визит"),
            ]
            for code, title, process_code, description, steps in outcomes:
                db.add(
                    OutcomeCatalogItem(
                        salon_id=salon.id,
                        outcome_code=code,
                        title=title,
                        process_code=process_code,
                        description=description,
                        event_storming_steps=steps,
                    )
                )
        db.commit()


app.include_router(web_admin_router)
app.include_router(v1_router)


@app.get("/")
async def root() -> dict:
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}
