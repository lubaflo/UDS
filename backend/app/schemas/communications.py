from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CommunicationStepIn(BaseModel):
    step_order: int = Field(ge=1)
    channel: str = Field(pattern="^(sms|app|email)$")
    subject: str = Field(default="", max_length=200)
    body: str = Field(min_length=1, max_length=4000)
    delay_minutes: int = Field(default=0, ge=0, le=60 * 24 * 30)


class CommunicationCampaignCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    purpose: str = Field(default="marketing", pattern="^(marketing|reminder)$")
    audience_type: str = Field(default="consented_marketing", pattern="^(all|consented_marketing|segment)$")
    schedule_type: str = Field(default="manual", pattern="^(manual|scheduled)$")
    schedule_at: int | None = None
    steps: list[CommunicationStepIn] = Field(min_length=1, max_length=20)


class CommunicationStepOut(BaseModel):
    id: int
    step_order: int
    channel: str
    subject: str
    body: str
    delay_minutes: int


class CommunicationCampaignOut(BaseModel):
    id: int
    title: str
    purpose: str
    audience_type: str
    status: str
    schedule_type: str
    schedule_at: int | None
    created_at: int
    steps: list[CommunicationStepOut]


class CommunicationCampaignListResponse(BaseModel):
    items: list[CommunicationCampaignOut]
    active_count: int
    archived_count: int


class CommunicationLaunchResponse(BaseModel):
    campaign_id: int
    selected_clients: int
    queued_recipients: int


class CommunicationTrackRequest(BaseModel):
    recipient_id: int
    event: str = Field(pattern="^(open|click|conversion)$")


class CommunicationStatsOut(BaseModel):
    campaign_id: int
    total: int
    sent: int
    opened: int
    clicked: int
    converted: int
    open_rate: float
    click_rate: float
    conversion_rate: float


class ReminderRuleIn(BaseModel):
    offset_minutes: Literal[60, 240, 1440, 10080]
    channel: str = Field(pattern="^(sms|app|email)$")
    is_enabled: bool = True


class ReminderRulesUpdateRequest(BaseModel):
    rules: list[ReminderRuleIn] = Field(min_length=1, max_length=12)


class ReminderRuleOut(BaseModel):
    id: int
    offset_minutes: int
    channel: str
    is_enabled: bool


class ReminderRulesResponse(BaseModel):
    items: list[ReminderRuleOut]


class AppointmentCreateRequest(BaseModel):
    client_id: int
    title: str = Field(default="Процедура", max_length=200)
    starts_at: int


class AppointmentOut(BaseModel):
    id: int
    client_id: int
    title: str
    starts_at: int
    status: str


class ReminderRunResponse(BaseModel):
    processed: int
    sent: int
    skipped: int


# Wizard Step 1..5
class WorkflowCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class WorkflowStep1AudienceRequest(BaseModel):
    purpose: str = Field(default="marketing", pattern="^(marketing|reminder)$")
    audience_type: str = Field(default="consented_marketing", pattern="^(all|consented_marketing|segment)$")


class WorkflowStep2ContentRequest(BaseModel):
    steps: list[CommunicationStepIn] = Field(min_length=1, max_length=20)


class WorkflowStep3ScheduleRequest(BaseModel):
    schedule_type: str = Field(default="manual", pattern="^(manual|scheduled)$")
    schedule_at: int | None = None


class WorkflowStep4ConfirmationResponse(BaseModel):
    campaign_id: int
    title: str
    purpose: str
    audience_type: str
    schedule_type: str
    schedule_at: int | None
    steps_count: int
    estimated_recipients: int


class WorkflowStateResponse(BaseModel):
    campaign_id: int
    current_step: int
    can_confirm: bool
    has_audience: bool
    has_content: bool
    has_schedule: bool


class WorkflowStep5StatsResponse(BaseModel):
    campaign_id: int
    total: int
    sent: int
    opened: int
    clicked: int
    converted: int
    open_rate: float
    click_rate: float
    conversion_rate: float
