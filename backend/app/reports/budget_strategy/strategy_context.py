from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.reports.budget_strategy.schemas import BudgetStrategyGenerateRequest


def normalize_value(value: str) -> str:
    """Normalize one strategy value.
    Args:
        value (str): Raw strategy value."""
    normalized_value = value.strip().lower()
    if normalized_value in {'', 'all'}:
        return 'all'
    if normalized_value == 'none':
        return 'none'
    values = sorted({item.strip() for item in value.split(',') if item.strip()})
    return ','.join(values) if values else 'all'


def normalize_amount(value: Decimal) -> str:
    """Normalize decimal budget amount.
    Args:
        value (Decimal): Raw budget amount."""
    return str(value.quantize(Decimal('0.01')))


def build_context(
    project_id: UUID,
    country_id: int,
    scope: str,
    request: BudgetStrategyGenerateRequest,
) -> dict[str, Any]:
    """Build normalized strategy context.
    Args:
        project_id (UUID): Project identifier.
        country_id (int): Target country identifier.
        scope (str): Analytical scope.
        request (BudgetStrategyGenerateRequest): Strategy request."""
    return {
        'strategy_mode': request.strategy_mode,
        'project_id': str(project_id),
        'country_id': country_id,
        'date_from': request.date_from.isoformat(),
        'date_to': request.date_to.isoformat(),
        'budget_amount': normalize_amount(request.budget_amount),
        'currency': request.currency,
        'company': normalize_value(request.company),
        'company_domain': normalize_value(request.company_domain),
        'competitors': normalize_value(request.competitors),
        'competitor_domain': normalize_value(request.competitor_domain),
        'tld': normalize_value(request.tld),
        'scope': scope,
        'calculation_version': request.calculation_version,
    }


def hash_context(context: dict[str, Any]) -> str:
    """Build stable context hash.
    Args:
        context (dict[str, Any]): Normalized context object."""
    serialized_context = json.dumps(context, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized_context.encode('utf-8')).hexdigest()
