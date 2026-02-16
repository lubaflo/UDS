from __future__ import annotations

from pydantic import BaseModel, Field


class SystemSettingsOut(BaseModel):
    weekly_report_enabled: bool
    global_search_enabled: bool
    responsible_first_name: str
    responsible_last_name: str
    responsible_phone: str
    avg_purchases_per_day: int


class SystemSettingsUpdateRequest(BaseModel):
    weekly_report_enabled: bool
    global_search_enabled: bool = False
    responsible_first_name: str = Field(default="", max_length=100)
    responsible_last_name: str = Field(default="", max_length=100)
    responsible_phone: str = Field(default="", max_length=32)
    avg_purchases_per_day: int = Field(ge=0, le=100000)
