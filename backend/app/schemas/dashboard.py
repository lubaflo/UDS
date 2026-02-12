from __future__ import annotations

from pydantic import BaseModel, Field


class FinanceStats(BaseModel):
    turnover_rub: int
    income_rub: int
    discount_rub: int


class BuyersStats(BaseModel):
    total: int
    new: int
    digitized: int


class OperationsStats(BaseModel):
    purchases_count: int
    orders_count: int
    refunds_count: int


class DashboardSummaryResponse(BaseModel):
    finance: FinanceStats
    buyers: BuyersStats
    operations: OperationsStats
    clients_count: int


class DashboardAlert(BaseModel):
    code: str
    level: str
    title: str
    subtitle: str
    action_label: str
    action_route: str


class DashboardPromoCard(BaseModel):
    code: str
    title: str
    subtitle: str
    action_label: str
    action_route: str


class DashboardSectionLink(BaseModel):
    section: str
    route: str
    children: list["DashboardSectionLink"] = Field(default_factory=list)


class DashboardFullResponse(BaseModel):
    summary: DashboardSummaryResponse
    section_links: list[DashboardSectionLink]
    alerts: list[DashboardAlert]
    promo_cards: list[DashboardPromoCard]
