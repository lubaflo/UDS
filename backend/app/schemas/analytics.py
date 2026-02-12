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
