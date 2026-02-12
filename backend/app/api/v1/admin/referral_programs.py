from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.referral_program import ReferralProgramGenerationRule, ReferralProgramSetting
from app.schemas.referral_programs import (
    ReferralClientInfoResponse,
    ReferralClientTierInfo,
    ReferralGenerationRule,
    ReferralProgramListItem,
    ReferralProgramListResponse,
    ReferralProgramSettingsOut,
    ReferralProgramSettingsUpdateRequest,
)
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/referral-programs", tags=["admin.referral_programs"])


def _default_rules() -> list[ReferralGenerationRule]:
    defaults = [10.0, 5.0, 3.0, 2.0, 1.0, 0.5]
    return [
        ReferralGenerationRule(generation=i + 1, reward_percent=defaults[i], is_enabled=i < 3)
        for i in range(6)
    ]


def _get_or_create_setting(db: Session, salon_id: int) -> ReferralProgramSetting:
    setting = db.execute(
        select(ReferralProgramSetting).where(ReferralProgramSetting.salon_id == salon_id)
    ).scalar_one_or_none()
    if setting is None:
        setting = ReferralProgramSetting(
            salon_id=salon_id,
            is_active=False,
            reward_unit="points",
            base_reward_value=100,
            max_generations=3,
        )
        db.add(setting)
        db.flush()
        for rule in _default_rules():
            db.add(
                ReferralProgramGenerationRule(
                    setting_id=setting.id,
                    generation=rule.generation,
                    reward_percent=rule.reward_percent,
                    is_enabled=rule.is_enabled,
                )
            )
        db.flush()
    return setting


def _get_rules(db: Session, setting_id: int) -> list[ReferralProgramGenerationRule]:
    return db.execute(
        select(ReferralProgramGenerationRule)
        .where(ReferralProgramGenerationRule.setting_id == setting_id)
        .order_by(ReferralProgramGenerationRule.generation.asc())
    ).scalars().all()


def _settings_to_response(db: Session, setting: ReferralProgramSetting) -> ReferralProgramSettingsOut:
    rules = _get_rules(db, setting.id)
    return ReferralProgramSettingsOut(
        is_active=setting.is_active,
        reward_unit=setting.reward_unit,
        base_reward_value=setting.base_reward_value,
        max_generations=setting.max_generations,
        generation_rules=[
            ReferralGenerationRule(
                generation=r.generation,
                reward_percent=r.reward_percent,
                is_enabled=r.is_enabled and r.generation <= setting.max_generations,
            )
            for r in rules
        ],
    )


@router.get("", response_model=ReferralProgramListResponse)
def list_referral_programs(
    ctx=Depends(require_roles("owner", "admin")),
) -> ReferralProgramListResponse:
    _ = ctx
    return ReferralProgramListResponse(
        items=[
            ReferralProgramListItem(
                code="mlm_referrals",
                title="Реферальная программа",
                description=(
                    "Настройка до 6 поколений рекомендаций: тип вознаграждения (баллы/деньги), "
                    "лимит поколений и % начисления по каждой очереди."
                ),
                route="/admin/referral-programs/config",
            )
        ]
    )


@router.get("/config", response_model=ReferralProgramSettingsOut)
def get_referral_program_config(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ReferralProgramSettingsOut:
    setting = _get_or_create_setting(db, ctx.salon_id)
    return _settings_to_response(db, setting)


@router.put("/config", response_model=ReferralProgramSettingsOut)
def update_referral_program_config(
    req: ReferralProgramSettingsUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ReferralProgramSettingsOut:
    setting = _get_or_create_setting(db, ctx.salon_id)

    setting.is_active = req.is_active
    setting.reward_unit = req.reward_unit
    setting.base_reward_value = req.base_reward_value
    setting.max_generations = req.max_generations

    current_rules = {r.generation: r for r in _get_rules(db, setting.id)}
    requested_rules = {r.generation: r for r in req.generation_rules}

    for generation in range(1, 7):
        incoming = requested_rules.get(generation)
        if generation not in current_rules:
            current_rules[generation] = ReferralProgramGenerationRule(
                setting_id=setting.id,
                generation=generation,
                reward_percent=0,
                is_enabled=False,
            )
            db.add(current_rules[generation])

        row = current_rules[generation]
        if incoming is None:
            row.reward_percent = 0
            row.is_enabled = False
            continue

        row.reward_percent = incoming.reward_percent
        row.is_enabled = incoming.is_enabled and generation <= req.max_generations

    write_audit(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        action="referral_program.update",
        entity="referral_program",
        entity_id=str(setting.id),
    )
    db.flush()
    return _settings_to_response(db, setting)


@router.get("/client-info", response_model=ReferralClientInfoResponse)
def get_referral_program_client_info(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ReferralClientInfoResponse:
    setting = _get_or_create_setting(db, ctx.salon_id)
    rules = _get_rules(db, setting.id)

    tiers: list[ReferralClientTierInfo] = []
    for rule in rules:
        if not rule.is_enabled or rule.generation > setting.max_generations:
            continue
        tiers.append(
            ReferralClientTierInfo(
                generation=rule.generation,
                generation_label=f"{rule.generation}-я очередь рекомендаций",
                reward_percent=rule.reward_percent,
                reward_value=round(setting.base_reward_value * rule.reward_percent / 100, 2),
                reward_unit=setting.reward_unit,
            )
        )

    return ReferralClientInfoResponse(
        is_active=setting.is_active,
        reward_unit=setting.reward_unit,
        max_generations=setting.max_generations,
        tiers=tiers,
    )
