from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.analytics.channel_intelligence import get_channel_intelligence
from app.analytics.country_intelligence import get_country_intelligence, resolve_project
from app.analytics.device_intelligence import get_device_intelligence
from app.reports.budget_strategy.calculators import build_allocation
from app.reports.budget_strategy.dependency_preparation import prepare_dependencies
from app.reports.budget_strategy.repository import (
    fetch_channel_profile,
    fetch_report,
    fetch_strategy_source,
    has_country_data,
    has_project_entity,
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
    DependencyStatus,
    StrategySource,
)
from app.reports.budget_strategy.strategy_context import build_context, hash_context


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


def resolve_source_scope(request: BudgetStrategyGenerateRequest, scope: str) -> str:
    """Resolve source scope for strategy mode.
    Args:
        request (BudgetStrategyGenerateRequest): Strategy request.
        scope (str): Requested analytical scope."""
    if request.strategy_mode == 'market_entry':
        return 'competitor' if request.competitors.lower() != 'none' else 'overall'
    return scope


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


def read_channel_scope(response: Any, request: BudgetStrategyGenerateRequest, scope: str) -> Any:
    """Read channel scope with market entry fallback.
    Args:
        response (Any): Grouped channel analytics response.
        request (BudgetStrategyGenerateRequest): Strategy request.
        scope (str): Requested scope."""
    scope_data = read_scope_data(response, scope)
    if (
        request.strategy_mode == 'market_entry'
        and scope == 'competitor'
        and scope_data is None
        and request.competitors.lower() == 'all'
    ):
        return response.overall_scope
    return scope_data


def read_device_scope(response: Any, request: BudgetStrategyGenerateRequest, scope: str) -> Any:
    """Read device scope with market entry fallback.
    Args:
        response (Any): Grouped device analytics response.
        request (BudgetStrategyGenerateRequest): Strategy request.
        scope (str): Requested scope."""
    scope_data = read_scope_data(response, scope)
    if (
        request.strategy_mode == 'market_entry'
        and scope == 'competitor'
        and scope_data is None
        and request.competitors.lower() == 'all'
    ):
        return response.overall_scope
    return scope_data


def build_device_snapshot(scope_data: Any, source: str) -> dict[str, Any]:
    """Build device source snapshot.
    Args:
        scope_data (Any): Device analytics scope.
        source (str): Snapshot source label."""
    if scope_data is None or scope_data.summary.visits_total <= 0:
        return {
            'source': source,
            'dominant_device': None,
            'desktop_share': None,
            'mobile_share': None,
            'desktop_quality_index': None,
            'mobile_quality_index': None,
            'desktop_bounce_rate': None,
            'mobile_bounce_rate': None,
            'desktop_avg_visit_duration': None,
            'mobile_avg_visit_duration': None,
        }
    return {
        'source': source,
        'dominant_device': scope_data.summary.dominant_device,
        'desktop_share': scope_data.summary.desktop_share,
        'mobile_share': scope_data.summary.mobile_share,
        'desktop_quality_index': scope_data.quality.desktop_quality_index,
        'mobile_quality_index': scope_data.quality.mobile_quality_index,
        'desktop_bounce_rate': scope_data.quality.desktop_bounce_rate,
        'mobile_bounce_rate': scope_data.quality.mobile_bounce_rate,
        'desktop_avg_visit_duration': scope_data.quality.desktop_duration,
        'mobile_avg_visit_duration': scope_data.quality.mobile_duration,
    }


def resolve_dominant_channel(channel_shares: dict[str, float]) -> str | None:
    """Resolve dominant channel from shares.
    Args:
        channel_shares (dict[str, float]): Channel share values."""
    if not channel_shares or sum(channel_shares.values()) <= 0:
        return None
    return max(channel_shares, key=channel_shares.get)


def build_strength_map(channel_shares: dict[str, float]) -> dict[str, str]:
    """Build channel strength map.
    Args:
        channel_shares (dict[str, float]): Channel share values."""
    strengths: dict[str, str] = {}
    for channel, share in channel_shares.items():
        if share >= 0.25:
            strengths[channel] = 'strong'
        elif share >= 0.05:
            strengths[channel] = 'proven'
        elif share > 0:
            strengths[channel] = 'weak'
        else:
            strengths[channel] = 'absent'
    return strengths


def build_channel_snapshot(scope_data: Any, source: str) -> dict[str, Any]:
    """Build channel source snapshot.
    Args:
        scope_data (Any): Channel analytics scope.
        source (str): Snapshot source label."""
    channel_shares = {
        item.channel: item.share
        for item in scope_data.channel_mix
    } if scope_data is not None else {}
    return {
        'source': source,
        'dominant_channel': scope_data.summary.dominant_channel if scope_data is not None else None,
        'total_traffic': scope_data.summary.total_traffic if scope_data is not None else 0,
        'channel_shares': channel_shares,
    }


def build_global_profile(
    channel_shares: dict[str, float],
    device_profile: dict[str, Any],
    country_data: Any,
) -> dict[str, Any]:
    """Build selected company global profile.
    Args:
        channel_shares (dict[str, float]): Company global channel shares.
        device_profile (dict[str, Any]): Company global device profile.
        country_data (Any): Company global country analytics."""
    profile_available = bool(channel_shares) or device_profile.get('dominant_device') is not None
    return {
        'available': profile_available,
        'channel_shares': channel_shares,
        'dominant_channel': resolve_dominant_channel(channel_shares),
        'channel_strengths': build_strength_map(channel_shares),
        'device_profile': device_profile,
        'traffic_quality': {
            'total_traffic': country_data.summary.total_traffic if country_data is not None else 0,
            'bounce_rate': country_data.bounce.bounce_rate if country_data is not None else None,
            'avg_visit_duration': country_data.engagement.avg_visit_duration if country_data is not None else None,
            'pages_per_visit': country_data.engagement.pages_per_visit if country_data is not None else None,
        },
    }


def build_device_note(scope_data: Any) -> str | None:
    """Build market entry device note.
    Args:
        scope_data (Any): Device analytics scope."""
    if scope_data is None or scope_data.summary.visits_total <= 0:
        return None
    if (
        scope_data.summary.desktop_share >= 0.55
        and scope_data.quality.desktop_duration >= scope_data.quality.mobile_duration
    ):
        return (
            'Desktop-heavy entry context: prioritize channels that capture research and high-intent traffic, '
            'and validate mobile traffic quality before scaling mobile-heavy campaigns.'
        )
    if (
        scope_data.summary.mobile_share >= 0.55
        and scope_data.quality.mobile_quality_index >= scope_data.quality.desktop_quality_index
    ):
        return (
            'Mobile-led entry context: validate fast mobile journeys and keep creative tests focused on '
            'mobile traffic quality.'
        )
    return 'Balanced device context: monitor desktop and mobile quality before shifting budget by device.'


def normalize_score_status(
    dependency_status: DependencyStatus,
    source: StrategySource,
    fallback_score: float,
) -> DependencyStatus:
    """Normalize opportunity score dependency status.
    Args:
        dependency_status (DependencyStatus): Initial dependency status.
        source (StrategySource): Strategy source data.
        fallback_score (float): Neutral fallback score."""
    score_status = dependency_status.opportunity_score
    fallbacks_used = [
        fallback_name
        for fallback_name in dependency_status.fallbacks_used
        if fallback_name != 'opportunity_score'
    ]
    if source.opportunity_score is not None:
        score_status.used_in_report = True
        score_status.is_fallback = False
        score_status.score = source.opportunity_score
        if score_status.status in {'failed', 'skipped', 'fallback_used'}:
            score_status.status = 'existing'
            score_status.message = 'A valid existing Opportunity Score was reused for the current context.'
        elif score_status.message is None:
            score_status.message = 'Opportunity Score was recalculated for the current context.'
    else:
        score_status.used_in_report = True
        score_status.is_fallback = True
        score_status.score = fallback_score
        score_status.status = 'fallback_used'
        score_status.message = (
            'No valid persisted Opportunity Score was available; a neutral fallback score was used.'
        )
        fallbacks_used.append('opportunity_score')
    dependency_status.opportunity_score = score_status
    dependency_status.fallbacks_used = sorted(set(fallbacks_used))
    return dependency_status


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
    source_scope = resolve_source_scope(request, scope)
    company_specific = request.company.lower() not in {'all', 'none'} or request.company_domain.lower() != 'all'
    company_has_country_data = has_country_data(
        session,
        project_id,
        country_id,
        request.date_from,
        request.date_to,
        request.company,
        request.company_domain,
        request.tld,
    )
    country_has_market_data = has_country_data(
        session,
        project_id,
        country_id,
        request.date_from,
        request.date_to,
        'all',
        'all',
        request.tld,
    )
    if request.strategy_mode == 'existing_presence' and company_specific and not company_has_country_data:
        raise ValueError('Selected company has no data in the target country. Use Market Entry Strategy instead.')
    if request.strategy_mode == 'existing_presence' and not country_has_market_data:
        raise ValueError('Target country has insufficient source data for Existing Presence Strategy.')
    if request.strategy_mode == 'market_entry':
        if not company_specific:
            raise ValueError('Target company or company domain is required for Market Entry Strategy.')
        if not has_project_entity(session, project_id, request.company, request.company_domain, request.tld):
            raise ValueError('Selected company was not found in the project.')
        if not country_has_market_data:
            raise ValueError('Target country has insufficient market or competitor data for Market Entry Strategy.')
    context_json = build_context(project_id, country_id, source_scope, request)
    context_hash = hash_context(context_json)
    dependency_status = prepare_dependencies(session, default_project_id, request, source_scope, context_hash, context_json)
    source = fetch_strategy_source(
        session,
        project_id,
        country_id,
        request.date_from,
        request.date_to,
        source_scope,
        request.calculation_version,
        context_hash,
    )
    dependency_status = normalize_score_status(dependency_status, source, 50.0)
    analytics_company = 'all' if request.strategy_mode == 'market_entry' else request.company
    analytics_company_domain = 'all' if request.strategy_mode == 'market_entry' else request.company_domain
    common = {
        'session': session,
        'default_project_id': default_project_id,
        'project_id': None,
        'date_from': request.date_from,
        'date_to': request.date_to,
        'country': request.country,
        'tld': request.tld,
        'company': analytics_company,
        'company_domain': analytics_company_domain,
        'competitors': request.competitors,
        'competitor_domain': request.competitor_domain,
        'limit': 10,
    }
    country_data = get_country_intelligence(**common)
    channel_data = get_channel_intelligence(**common)
    device_data = get_device_intelligence(**common)
    company_global_country_data = (
        get_country_intelligence(
            session=session,
            default_project_id=default_project_id,
            project_id=None,
            date_from=request.date_from,
            date_to=request.date_to,
            country='all',
            tld=request.tld,
            company=request.company,
            company_domain=request.company_domain,
            competitors='none',
            competitor_domain='all',
            limit=10,
        )
        if request.strategy_mode == 'market_entry'
        else None
    )
    company_global_device_data = (
        get_device_intelligence(
            session=session,
            default_project_id=default_project_id,
            project_id=None,
            date_from=request.date_from,
            date_to=request.date_to,
            country='all',
            tld=request.tld,
            company=request.company,
            company_domain=request.company_domain,
            competitors='none',
            competitor_domain='all',
            limit=10,
        )
        if request.strategy_mode == 'market_entry'
        else None
    )
    country_summary = country_data.competitor_summary if source_scope == 'competitor' else country_data.summary
    country_bounce = country_data.competitor_bounce if source_scope == 'competitor' else country_data.bounce
    country_engagement = country_data.competitor_engagement if source_scope == 'competitor' else country_data.engagement
    market_signal = (
        country_data.competitor_market_signal
        if source_scope == 'competitor'
        else country_data.market_signal
    )
    channel_scope = read_channel_scope(channel_data, request, source_scope)
    use_market_channel_scope = (
        request.strategy_mode == 'market_entry'
        and source_scope == 'competitor'
        and request.competitors.lower() == 'all'
    )
    competitor_scope = channel_data.competitor_scope or (channel_scope if use_market_channel_scope else None)
    device_scope = read_device_scope(device_data, request, source_scope)
    company_global_device_scope = (
        company_global_device_data.company_scope
        if company_global_device_data is not None
        else None
    )
    quality_score = calculate_quality(
        country_bounce.bounce_rate,
        country_engagement.avg_visit_duration,
        country_engagement.pages_per_visit,
    )
    stability_score = 50.0 if not source.signal_types else 35.0 if 'channel_shift' in source.signal_types else 80.0
    opportunity_modifier = dependency_status.opportunity_score.score or 50.0
    market_shares = {item.channel: item.share for item in channel_scope.channel_mix} if channel_scope else {}
    competitor_shares = {item.channel: item.share for item in competitor_scope.channel_mix} if competitor_scope else {}
    company_global_shares = (
        fetch_channel_profile(
            session,
            project_id,
            request.date_from,
            request.date_to,
            request.company,
            request.company_domain,
            request.tld,
        )
        if request.strategy_mode == 'market_entry'
        else {}
    )
    high_risk_signals = {'traffic_quality_degradation', 'mobile_growth_low_quality', 'high_volatility'}
    channels = [
        ChannelInput(
            channel=channel,
            market_share=market_shares.get(channel, 0.0),
            competitor_share=competitor_shares.get(channel, 0.0),
            company_global_share=company_global_shares.get(channel, 0.0),
            quality_score=quality_score,
            stability_score=stability_score,
            opportunity_modifier=opportunity_modifier,
            high_risk=bool(high_risk_signals.intersection(source.signal_types)) and channel in {'paid', 'social'},
        )
        for channel in CHANNELS
    ]
    result = build_allocation(
        channels,
        request.budget_amount,
        source.signal_types,
        source.opportunity_risks,
        request.strategy_mode,
        company_has_country_data,
    )
    device_source = 'target_country_market' if request.strategy_mode == 'market_entry' else source_scope
    channel_source = 'target_country_market' if request.strategy_mode == 'market_entry' else source_scope
    channel_snapshot = build_channel_snapshot(channel_scope, channel_source)
    device_snapshot = build_device_snapshot(device_scope, device_source)
    company_global_device_snapshot = build_device_snapshot(
        company_global_device_scope,
        'selected_company_global',
    )
    company_global_profile = build_global_profile(
        company_global_shares,
        company_global_device_snapshot,
        company_global_country_data,
    )
    device_note = build_device_note(device_scope) if request.strategy_mode == 'market_entry' else None
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
        'channel_intelligence': channel_snapshot,
        'company_global_profile': company_global_profile,
        'device_intelligence': device_snapshot,
        'opportunity_score': {
            'score': dependency_status.opportunity_score.score,
            'status': dependency_status.opportunity_score.status,
            'used_in_report': dependency_status.opportunity_score.used_in_report,
            'is_fallback': dependency_status.opportunity_score.is_fallback,
            'category': source.opportunity_category,
            'strengths': source.opportunity_strengths,
            'risks': source.opportunity_risks,
        },
        'signals': source.signal_types,
    }
    warnings = []
    if 'signals' in dependency_status.fallbacks_used:
        warnings.append('signals dependency could not be recalculated; fallback analytics were used.')
    if dependency_status.opportunity_score.status == 'fallback_used':
        warnings.append('Opportunity Score fallback was used because no valid persisted score was available.')
    if dependency_status.opportunity_score.status == 'failed':
        warnings.append('Opportunity Score is unavailable; allocation confidence is reduced.')
    if not source.signal_types:
        warnings.append('Derived signals are unavailable; direct analytics fallback is used.')
    if not channel_scope or not channel_scope.channel_mix:
        warnings.append('Channel data is unavailable; allocation confidence is low.')
    if device_scope is None or device_scope.summary.visits_total <= 0:
        warnings.append('Device intelligence is unavailable for the selected market context.')
    if request.strategy_mode == 'market_entry' and not company_has_country_data:
        warnings.append('The selected company has no existing traffic in this country; market-entry logic used market, competitor, and global company context.')
    recommended_approach = result.recommended_approach
    if request.strategy_mode == 'existing_presence':
        recommended_approach = f'Existing Presence Strategy: {recommended_approach}'
    else:
        recommended_approach = f'Market Entry Strategy: {recommended_approach}'
    payload = {
        'date_from': request.date_from,
        'date_to': request.date_to,
        'budget_amount': request.budget_amount,
        'currency': request.currency,
        'strategy_mode': request.strategy_mode,
        'scope': source_scope,
        'status': 'generated',
        'opportunity_score': dependency_status.opportunity_score.score,
        'opportunity_score_id': source.opportunity_score_id,
        'recommended_approach': recommended_approach,
        'allocation': [item.model_dump() for item in result.allocation],
        'channel_roles': result.channel_roles,
        'expected_effect': result.expected_effect.model_dump(),
        'risks': [risk.model_dump() for risk in result.risks],
        'explanation': {
            **result.explanation,
            'warnings': warnings,
            'device_note': device_note,
            'market_entry_no_target_country_data': request.strategy_mode == 'market_entry' and not company_has_country_data,
        },
        'dependency_status': dependency_status.model_dump(),
        'context_hash': context_hash,
        'context_json': context_json,
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
