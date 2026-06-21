from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field

BudgetChannelRole = Literal['priority', 'test', 'supporting', 'risky']


class BudgetStrategyGenerateRequest(BaseModel):
    date_from: date
    date_to: date
    country: str
    budget_amount: Decimal = Field(gt=0)
    currency: Literal['USD', 'EUR'] = 'USD'
    company: str = 'all'
    company_domain: str = 'all'
    competitors: str = 'all'
    competitor_domain: str = 'all'
    tld: str = 'all'
    calculation_version: str = 'v1'


class ChannelInput(BaseModel):
    channel: str
    market_share: float
    competitor_share: float
    quality_score: float
    stability_score: float
    opportunity_modifier: float
    high_risk: bool = False


class BudgetAllocationItem(BaseModel):
    channel: str
    role: BudgetChannelRole
    amount: float
    share: float
    score: float
    reason: str


class StrategyRisk(BaseModel):
    type: str
    severity: str
    message: str
    affected_channels: list[str]
    mitigation_hint: str


class ExpectedEffect(BaseModel):
    confidence: str
    expected_direction: str
    primary_effects: list[str]
    secondary_effects: list[str]
    measurement_focus: list[str]


class AllocationResult(BaseModel):
    allocation: list[BudgetAllocationItem]
    channel_roles: dict[str, list[str]]
    expected_effect: ExpectedEffect
    risks: list[StrategyRisk]
    explanation: dict[str, Any]
    recommended_approach: str


class BudgetStrategyReportResponse(BaseModel):
    id: int
    country: str
    country_code: str
    date_from: date
    date_to: date
    budget_amount: float
    currency: str
    scope: str
    status: str
    opportunity_score: float | None
    recommended_approach: str
    allocation: list[BudgetAllocationItem]
    channel_roles: dict[str, list[str]]
    expected_effect: ExpectedEffect
    risks: list[StrategyRisk]
    explanation: dict[str, Any]
    source_snapshot: dict[str, Any]
    calculation_version: str
    created_at: datetime


class BudgetStrategyListResponse(BaseModel):
    items: list[BudgetStrategyReportResponse]


class StrategySource(BaseModel):
    country_id: int
    country: str
    country_code: str
    scope: str
    opportunity_score_id: int | None
    opportunity_score: float | None
    opportunity_category: str | None
    opportunity_strengths: list[str]
    opportunity_risks: list[str]
    signal_types: list[str]
