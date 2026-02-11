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
