from datetime import date
from typing import Any

from pydantic import BaseModel


class SignalCandidate(BaseModel):
    signal_type: str
    signal_group: str
    entity_type: str
    entity_id: str | None = None
    country_id: int | None = None
    company_id: int | None = None
    domain_id: int | None = None
    date_from: date
    date_to: date
    severity: str
    scope: str = 'overall'
    score: float | None = None
    value: float | None = None
    baseline_value: float | None = None
    delta_value: float | None = None
    delta_percent: float | None = None
    message: str
    details: dict[str, Any]
    calculation_version: str
