from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ClientChildOut(BaseModel):
    id: int
    full_name: str
    birth_date: str
    notes: str


class ClientChildInput(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    birth_date: str = Field(default="", max_length=10)
    notes: str = Field(default="", max_length=500)


class ClientLoyaltyProgramOut(BaseModel):
    id: int
    program_name: str
    status: str
    level_name: str
    balance: int
    expires_at: int | None


class ClientLoyaltyProgramInput(BaseModel):
    program_name: str = Field(min_length=1, max_length=200)
    status: str = Field(default="active", max_length=32)
    level_name: str = Field(default="", max_length=120)
    balance: int = 0
    expires_at: int | None = None


class ClientGroupRuleOut(BaseModel):
    id: int
    group_name: str
    is_active: bool
    min_visits: int
    min_total_spent_rub: int
    inactive_days_over: int
    require_marketing_consent: bool


class ClientGroupRuleInput(BaseModel):
    group_name: str = Field(min_length=1, max_length=120)
    is_active: bool = True
    min_visits: int = Field(default=0, ge=0)
    min_total_spent_rub: int = Field(default=0, ge=0)
    inactive_days_over: int = Field(default=0, ge=0)
    require_marketing_consent: bool = False


class ClientOut(BaseModel):
    id: int
    tg_id: int | None
    username: str
    full_name: str
    phone: str
    whatsapp_phone: str
    email: str
    telegram_username: str
    vk_username: str
    instagram_username: str
    facebook_username: str
    max_username: str
    address: str
    birthday: str
    status: str
    notes: str
    tags: list[str] = Field(default_factory=list)
    acquisition_channel_id: int | None
    visits_count: int
    total_spent_rub: int
    last_visit_at: int | None
    gender: str
    birth_year: int | None
    consent_personal_data: bool
    consent_marketing: bool
    consent_sms: bool
    consent_app_push: bool
    consent_email: bool


class ClientCardOut(BaseModel):
    client: ClientOut
    groups: list[str] = Field(default_factory=list)
    children: list[ClientChildOut] = Field(default_factory=list)
    loyalty_programs: list[ClientLoyaltyProgramOut] = Field(default_factory=list)
    visit_history: list[dict] = Field(default_factory=list)
    purchase_history: list[dict] = Field(default_factory=list)


class ClientListResponse(BaseModel):
    items: list[ClientOut]
    page: int
    page_size: int
    total: int


class _EmailMixin(BaseModel):
    @field_validator("email", check_fields=False)
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if "@" not in value:
            raise ValueError("email must contain @")
        return value


class ClientCreateRequest(_EmailMixin):
    tg_id: int | None = None
    username: str = ""
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(default="", max_length=32)
    whatsapp_phone: str = Field(default="", max_length=32)
    email: str | None = None
    telegram_username: str = Field(default="", max_length=128)
    vk_username: str = Field(default="", max_length=128)
    instagram_username: str = Field(default="", max_length=128)
    facebook_username: str = Field(default="", max_length=128)
    max_username: str = Field(default="", max_length=128)
    address: str = Field(default="", max_length=400)
    birthday: str = Field(default="", max_length=10)
    notes: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list)
    acquisition_channel_id: int | None = None
    gender: str = Field(default="unknown", pattern="^(male|female|unknown)$")
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    consent_personal_data: bool = False
    consent_marketing: bool = False
    consent_sms: bool = False
    consent_app_push: bool = False
    consent_email: bool = False
    children: list[ClientChildInput] = Field(default_factory=list)
    loyalty_programs: list[ClientLoyaltyProgramInput] = Field(default_factory=list)


class ClientUpdateRequest(_EmailMixin):
    username: str | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    whatsapp_phone: str | None = Field(default=None, max_length=32)
    email: str | None = None
    telegram_username: str | None = Field(default=None, max_length=128)
    vk_username: str | None = Field(default=None, max_length=128)
    instagram_username: str | None = Field(default=None, max_length=128)
    facebook_username: str | None = Field(default=None, max_length=128)
    max_username: str | None = Field(default=None, max_length=128)
    address: str | None = Field(default=None, max_length=400)
    birthday: str | None = Field(default=None, max_length=10)
    status: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = None
    acquisition_channel_id: int | None = None
    gender: str | None = Field(default=None, pattern="^(male|female|unknown)$")
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    consent_personal_data: bool | None = None
    consent_marketing: bool | None = None
    consent_sms: bool | None = None
    consent_app_push: bool | None = None
    consent_email: bool | None = None
    children: list[ClientChildInput] | None = None
    loyalty_programs: list[ClientLoyaltyProgramInput] | None = None


class ClientGroupRulesResponse(BaseModel):
    items: list[ClientGroupRuleOut]
