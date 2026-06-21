from datetime import date
from typing import Any

from pydantic import BaseModel


class CountryMetric(BaseModel):
    country_id: int
    country: str
    country_code: str
    total_traffic: int
    first_traffic: int
    second_traffic: int
    active_companies: int
    active_domains: int
    top1_share: float
    top3_share: float
    bounce_rate: float
    avg_visit_duration: float
    pages_per_visit: float


class FactorResult(BaseModel):
    factor: str
    raw_value: Any
    score: float
    weight: float
    weighted_score: float
    status: str
    explanation: str


class ScoreCandidate(BaseModel):
    country_id: int
    country: str
    country_code: str
    scope: str
    date_from: date
    date_to: date
    opportunity_score: float
    score_category: str
    rank: int | None = None
    factors: list[FactorResult]
    strengths: list[str]
    weaknesses: list[str]
    risks: list[str]
    explanation: dict[str, Any]
    details: dict[str, Any]
    calculation_version: str
