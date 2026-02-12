from __future__ import annotations

from pydantic import BaseModel, Field


class ReferralGenerationRule(BaseModel):
    generation: int = Field(ge=1, le=6)
    reward_percent: float = Field(ge=0, le=100)
    is_enabled: bool = True


class ReferralProgramSettingsOut(BaseModel):
    is_active: bool
    reward_unit: str = Field(pattern="^(points|money)$")
    base_reward_value: int = Field(ge=0)
    max_generations: int = Field(ge=1, le=6)
    generation_rules: list[ReferralGenerationRule]


class ReferralProgramSettingsUpdateRequest(BaseModel):
    is_active: bool
    reward_unit: str = Field(pattern="^(points|money)$")
    base_reward_value: int = Field(ge=0, le=1_000_000)
    max_generations: int = Field(ge=1, le=6)
    generation_rules: list[ReferralGenerationRule] = Field(default_factory=list, min_length=1, max_length=6)


class ReferralProgramListItem(BaseModel):
    code: str
    title: str
    description: str
    route: str


class ReferralProgramListResponse(BaseModel):
    items: list[ReferralProgramListItem] = Field(default_factory=list)


class ReferralClientTierInfo(BaseModel):
    generation: int
    generation_label: str
    reward_percent: float
    reward_value: float
    reward_unit: str


class ReferralClientInfoResponse(BaseModel):
    is_active: bool
    reward_unit: str
    max_generations: int
    tiers: list[ReferralClientTierInfo]
