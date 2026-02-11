from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ClientOut(BaseModel):
    id: int
    tg_id: int | None
    username: str
    full_name: str
    phone: str
    email: str
    vk_username: str
    instagram_username: str
    facebook_username: str
    max_username: str
    address: str
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
    email: str | None = None
    vk_username: str = Field(default="", max_length=128)
    instagram_username: str = Field(default="", max_length=128)
    facebook_username: str = Field(default="", max_length=128)
    max_username: str = Field(default="", max_length=128)
    address: str = Field(default="", max_length=400)
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


class ClientUpdateRequest(_EmailMixin):
    username: str | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = None
    vk_username: str | None = Field(default=None, max_length=128)
    instagram_username: str | None = Field(default=None, max_length=128)
    facebook_username: str | None = Field(default=None, max_length=128)
    max_username: str | None = Field(default=None, max_length=128)
    address: str | None = Field(default=None, max_length=400)
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
