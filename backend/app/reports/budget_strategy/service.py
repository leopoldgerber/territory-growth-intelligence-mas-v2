from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.analytics.channel_intelligence import get_channel_intelligence
from app.analytics.country_intelligence import get_country_intelligence, resolve_project
from app.analytics.device_intelligence import get_device_intelligence
from app.reports.budget_strategy.calculators import build_allocation
from app.reports.budget_strategy.repository import (
    fetch_report,
    fetch_strategy_source,
    resolve_country,
    save_report,
    select_reports,
    serialize_report,
)
from app.reports.budget_strategy.schemas import (
    BudgetStrategyGenerateRequest,
    BudgetStrategyListResponse,
    BudgetStrategyReportResponse,
    ChannelInput,
)

CHANNELS = ('search', 'paid', 'referral', 'social', 'direct')


def resolve_scope(request: BudgetStrategyGenerateRequest) -> str:
    """Resolve primary strategy scope.
    Args:
        request (BudgetStrategyGenerateRequest): Strategy request."""
    company_explicit = request.company.lower() not in {'all', 'none'} or request.company_domain.lower() != 'all'
    competitor_explicit = (
        request.competitors.lower() not in {'all', 'none'}
        or request.competitor_domain.lower() != 'all'
    )
    if company_explicit or (request.company.lower() != 'none' and request.competitors.lower() == 'none'):
        return 'company'
    if competitor_explicit or request.company.lower() == 'none':
        return 'competitor'
    return 'overall'


def read_scope_data(response: Any, scope: str) -> Any:
    """Read one scope from grouped analytics response.
    Args:
        response (Any): Grouped analytics response.
        scope (str): Requested scope."""
    if scope == 'company':
        return response.company_scope
    if scope == 'competitor':
        return response.competitor_scope
    return response.overall_scope


def calculate_quality(bounce_rate: float, duration: float, pages: float) -> float:
    """Calculate normalized traffic quality.
    Args:
        bounce_rate (float): Traffic bounce rate.
        duration (float): Average visit duration.
        pages (float): Average pages per visit."""
    return min(max(duration / 180, 0), 1) * 35 + min(max(1 - bounce_rate, 0), 1) * 45 + min(max(pages / 5, 0), 1) * 20


def generate_strategy(
    session: Session,
    default_project_id: str,
    request: BudgetStrategyGenerateRequest,
) -> BudgetStrategyReportResponse:
    """Generate and persist budget strategy report.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        request (BudgetStrategyGenerateRequest): Strategy request."""
    if request.date_from > request.date_to:
        raise ValueError('date_from must be before or equal to date_to')
    if request.country.lower() == 'all' or ',' in request.country:
        raise ValueError('exactly one country is required')
    project_id = resolve_project(None, default_project_id)
    country_id, country_name, country_code = resolve_country(session, request.country)
    scope = resolve_scope(request)
    source = fetch_strategy_source(
        session, project_id, country_id, request.date_from, request.date_to, scope, request.calculation_version
    )
    common = {
        'session': session,
        'default_project_id': default_project_id,
        'project_id': None,
        'date_from': request.date_from,
        'date_to': request.date_to,
        'country': request.country,
        'tld': request.tld,
        'company': request.company,
        'company_domain': request.company_domain,
        'competitors': request.competitors,
        'competitor_domain': request.competitor_domain,
        'limit': 10,
    }
    country_data = get_country_intelligence(**common)
    channel_data = get_channel_intelligence(**common)
    device_data = get_device_intelligence(**common)
    country_summary = country_data.competitor_summary if scope == 'competitor' else country_data.summary
    country_bounce = country_data.competitor_bounce if scope == 'competitor' else country_data.bounce
    country_engagement = country_data.competitor_engagement if scope == 'competitor' else country_data.engagement
    market_signal = (
        country_data.competitor_market_signal
        if scope == 'competitor'
        else country_data.market_signal
    )
    channel_scope = read_scope_data(channel_data, scope)
    competitor_scope = channel_data.competitor_scope
    device_scope = read_scope_data(device_data, scope)
    quality_score = calculate_quality(
        country_bounce.bounce_rate,
        country_engagement.avg_visit_duration,
        country_engagement.pages_per_visit,
    )
    stability_score = 50.0 if not source.signal_types else 35.0 if 'channel_shift' in source.signal_types else 80.0
    opportunity_modifier = source.opportunity_score if source.opportunity_score is not None else 50.0
    market_shares = {item.channel: item.share for item in channel_scope.channel_mix} if channel_scope else {}
    competitor_shares = {item.channel: item.share for item in competitor_scope.channel_mix} if competitor_scope else {}
    high_risk_signals = {'traffic_quality_degradation', 'mobile_growth_low_quality', 'high_volatility'}
    channels = [
        ChannelInput(
            channel=channel,
            market_share=market_shares.get(channel, 0.0),
            competitor_share=competitor_shares.get(channel, 0.0),
            quality_score=quality_score,
            stability_score=stability_score,
            opportunity_modifier=opportunity_modifier,
            high_risk=bool(high_risk_signals.intersection(source.signal_types)) and channel in {'paid', 'social'},
        )
        for channel in CHANNELS
    ]
    result = build_allocation(channels, request.budget_amount, source.signal_types, source.opportunity_risks)
    device_snapshot = {
        'dominant_device': device_scope.summary.dominant_device if device_scope else None,
        'desktop_quality_index': device_scope.quality.desktop_quality_index if device_scope else None,
        'mobile_quality_index': device_scope.quality.mobile_quality_index if device_scope else None,
    }
    snapshot = {
        'country_intelligence': {
            'total_traffic': country_summary.total_traffic,
            'growth_rate': market_signal.growth_rate,
            'bounce_rate': country_bounce.bounce_rate,
            'avg_visit_duration': country_engagement.avg_visit_duration,
            'pages_per_visit': country_engagement.pages_per_visit,
        },
        'competitor_intelligence': {
            'total_traffic': country_data.competitor_summary.total_traffic,
            'growth_rate': country_data.competitor_market_signal.growth_rate,
            'active_competitors': country_data.competitor_summary.active_competitors,
        },
        'channel_intelligence': {
            'dominant_channel': channel_scope.summary.dominant_channel if channel_scope else None,
            'channel_shares': market_shares,
        },
        'device_intelligence': device_snapshot,
        'opportunity_score': {
            'score': source.opportunity_score,
            'category': source.opportunity_category,
            'strengths': source.opportunity_strengths,
            'risks': source.opportunity_risks,
        },
        'signals': source.signal_types,
    }
    warnings = []
    if source.opportunity_score is None:
        warnings.append('Opportunity score is unavailable; a neutral modifier is used.')
    if not source.signal_types:
        warnings.append('Derived signals are unavailable; direct analytics fallback is used.')
    if not channel_scope or not channel_scope.channel_mix:
        warnings.append('Channel data is unavailable; allocation confidence is low.')
    payload = {
        'date_from': request.date_from,
        'date_to': request.date_to,
        'budget_amount': request.budget_amount,
        'currency': request.currency,
        'scope': scope,
        'status': 'generated',
        'opportunity_score': source.opportunity_score,
        'opportunity_score_id': source.opportunity_score_id,
        'recommended_approach': result.recommended_approach,
        'allocation': [item.model_dump() for item in result.allocation],
        'channel_roles': result.channel_roles,
        'expected_effect': result.expected_effect.model_dump(),
        'risks': [risk.model_dump() for risk in result.risks],
        'explanation': {**result.explanation, 'warnings': warnings},
        'source_snapshot': snapshot,
        'calculation_version': request.calculation_version,
    }
    try:
        record = save_report(session, project_id, source, payload)
        session.commit()
        session.refresh(record)
    except Exception:
        session.rollback()
        raise
    return serialize_report(record, country_name, country_code)


def list_strategies(
    session: Session,
    default_project_id: str,
    date_from: date | None,
    date_to: date | None,
    country: str | None,
    scope: str | None,
    limit: int,
) -> BudgetStrategyListResponse:
    """List saved budget strategies.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str | None): Requested country.
        scope (str | None): Requested scope.
        limit (int): Result limit."""
    project_id = resolve_project(None, default_project_id)
    rows = select_reports(session, project_id, date_from, date_to, country, scope, limit)
    return BudgetStrategyListResponse(
        items=[serialize_report(record, name, code) for record, name, code in rows]
    )


def get_strategy(
    session: Session,
    default_project_id: str,
    report_id: int,
) -> BudgetStrategyReportResponse | None:
    """Get one saved budget strategy.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        report_id (int): Report identifier."""
    project_id = resolve_project(None, default_project_id)
    row = fetch_report(session, project_id, report_id)
    return serialize_report(*row) if row else None
