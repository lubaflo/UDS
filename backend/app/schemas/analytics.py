from __future__ import annotations

from pydantic import BaseModel, Field


class MetricCard(BaseModel):
    code: str
    title: str
    value: float | int


class DistributionItem(BaseModel):
    label: str
    value: int


class SeriesPoint(BaseModel):
    ts: int
    value: int | float


class CustomersAnalyticsResponse(BaseModel):
    cards: list[MetricCard]
    gender_distribution: list[DistributionItem]
    age_distribution: list[DistributionItem]
    new_clients_series: list[SeriesPoint]


class OperationsAnalyticsResponse(BaseModel):
    cards: list[MetricCard]
    operations_series: list[SeriesPoint]


class FinanceCategoryBreakdownItem(BaseModel):
    code: str
    title: str
    amount_rub: int
    share_percent: float


class FinanceAnalyticsResponse(BaseModel):
    cards: list[MetricCard]
    cashflow_series: list[SeriesPoint]
    income_by_source: list[FinanceCategoryBreakdownItem]
    expenses_by_source: list[FinanceCategoryBreakdownItem]


class RatingAnalyticsResponse(BaseModel):
    mode: str
    average_rating: float
    total_reviews: int
    distribution: list[DistributionItem]


class LevelsAnalyticsItem(BaseModel):
    level: str
    clients_total: int
    bought_clients: int
    not_bought_clients: int


class LevelsAnalyticsResponse(BaseModel):
    items: list[LevelsAnalyticsItem]


class AppVisitsAnalyticsResponse(BaseModel):
    mode: str
    detailing: str
    timezone: str
    info_text: str
    series: list[SeriesPoint]


class AnalyticsFilters(BaseModel):
    date_from: int | None = None
    date_to: int | None = None


class RatingModeRequest(BaseModel):
    mode: str = Field(pattern="^(payments|recommendations)$")


class PromotionForecastRequest(BaseModel):
    period_days: int = Field(default=30, ge=1, le=365)
    initial_clients: int = Field(default=100, ge=0, le=10_000_000)
    avg_check_rub: float = Field(default=1500, ge=0)
    conversion_rate_percent: float = Field(default=12, ge=0, le=100)
    gross_margin_percent: float = Field(default=35, ge=0, le=100)


class PromotionForecastGeneration(BaseModel):
    generation: int
    expected_new_clients: int
    expected_reward_cost_rub: float


class PromotionForecastResponse(BaseModel):
    period_days: int
    projected_clients_total: int
    projected_revenue_rub: float
    projected_gross_profit_rub: float
    projected_reward_cost_rub: float
    projected_net_effect_rub: float
    break_even_new_clients: int
    break_even_conversion_rate_percent: float
    generations: list[PromotionForecastGeneration]


class MarketingFunnelStage(BaseModel):
    code: str
    title: str
    clients: int
    conversion_percent: float


class MarketingChannelStats(BaseModel):
    channel_id: int | None
    channel_name: str
    clients_total: int
    buyers_total: int
    purchases_total: int
    revenue_rub: int
    conversion_to_purchase_percent: float


class MarketingSegment(BaseModel):
    segment: str
    clients_total: int
    buyers_total: int
    conversion_percent: float


class MarketingAutomationStats(BaseModel):
    campaigns_total: int
    sent_total: int
    opened_total: int
    clicked_total: int
    converted_total: int
    open_rate_percent: float
    click_rate_percent: float
    conversion_rate_percent: float


class MarketingForecastPoint(BaseModel):
    ts: int
    new_clients_actual: int
    new_clients_forecast: int


class MarketingAnalyticsResponse(BaseModel):
    cards: list[MetricCard]
    channels: list[MarketingChannelStats]
    funnel: list[MarketingFunnelStage]
    segments: list[MarketingSegment]
    automation: MarketingAutomationStats
    forecast: list[MarketingForecastPoint]
    insights: list[str]


class ControlTowerBookingStats(BaseModel):
    appointments_total: int
    appointments_completed: int
    appointments_cancelled: int
    no_show_risk_percent: float
    future_bookings_total: int
    future_bookings_revenue_forecast_rub: int


class ControlTowerInventoryStats(BaseModel):
    sku_total: int
    inventory_valuation_rub: int
    low_stock_positions: int
    out_of_stock_positions: int
    top_stock_items: list[MetricCard]


class ControlTowerSalesFunnelStage(BaseModel):
    code: str
    title: str
    clients: int
    conversion_percent: float


class ControlTowerActionItem(BaseModel):
    code: str
    title: str
    priority: str
    description: str


class ProcessKPIItem(BaseModel):
    process_code: str
    process_title: str
    kpi_name: str
    sla_name: str
    sla_target: float
    trigger_event: str
    baseline_value: float
    target_value: float
    unit: str
    current_value: float
    gap_to_target: float
    recommended_action: str
    is_enabled: bool
    auto_orchestration_enabled: bool


class ProcessKPIUpdateRequest(BaseModel):
    baseline_value: float | None = None
    target_value: float | None = None
    is_enabled: bool | None = None
    auto_orchestration_enabled: bool | None = None


class ControlTowerPolicyResponse(BaseModel):
    max_touches_per_week: int
    min_hours_between_touches: int
    channel_priority: list[str]
    min_phone_fill_percent: float
    min_consent_fill_percent: float
    enforce_quiet_hours: bool
    quiet_hours_start: int
    quiet_hours_end: int


class ControlTowerPolicyUpdateRequest(BaseModel):
    max_touches_per_week: int | None = Field(default=None, ge=1, le=30)
    min_hours_between_touches: int | None = Field(default=None, ge=1, le=168)
    channel_priority: list[str] | None = None
    min_phone_fill_percent: float | None = Field(default=None, ge=0, le=100)
    min_consent_fill_percent: float | None = Field(default=None, ge=0, le=100)
    enforce_quiet_hours: bool | None = None
    quiet_hours_start: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=None, ge=0, le=23)


class OnboardingGoalRequest(BaseModel):
    vertical: str = Field(pattern="^(salon|clinic|retail|fitness)$")
    goal_90d: str = Field(min_length=10, max_length=255)
    dashboard_focus: str = Field(min_length=5, max_length=255)


class OnboardingGoalResponse(BaseModel):
    vertical: str
    goal_90d: str
    dashboard_focus: str
    onboarding_completed: bool


class OutcomeCatalogItemResponse(BaseModel):
    outcome_code: str
    title: str
    process_code: str
    description: str
    event_storming_steps: list[str]


class VerticalPresetResponse(BaseModel):
    vertical: str
    title: str
    default_goal_90d: str
    kpi_defaults: list[MetricCard]
    process_codes: list[str]


class EndpointSpecItem(BaseModel):
    endpoint: str
    business_rules: list[str]
    exceptions: list[str]
    data_examples: list[dict[str, str | int | float]]


class ControlTowerAnalyticsResponse(BaseModel):
    cards: list[MetricCard]
    sales_funnel: list[ControlTowerSalesFunnelStage]
    bookings: ControlTowerBookingStats
    inventory: ControlTowerInventoryStats
    action_plan: list[ControlTowerActionItem]
    process_kpis: list[ProcessKPIItem]
    policy: ControlTowerPolicyResponse
    onboarding: OnboardingGoalResponse
