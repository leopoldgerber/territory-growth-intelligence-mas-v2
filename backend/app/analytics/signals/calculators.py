from statistics import pstdev
from typing import Any

from app.analytics.country_intelligence import divide_values
from app.analytics.signals.schemas import SignalCandidate

MIN_MARKET_TRAFFIC = 1000


def classify_severity(change_rate: float) -> str:
    """Classify signal severity.
    Args:
        change_rate (float): Absolute or signed change rate."""
    absolute_change = abs(change_rate)
    if absolute_change >= 0.50:
        return 'high'
    if absolute_change >= 0.25:
        return 'medium'
    return 'low'


def build_growth_signals(
    metrics: list[dict[str, Any]],
    calculation_version: str,
) -> list[SignalCandidate]:
    """Build traffic growth signals.
    Args:
        metrics (list[dict[str, Any]]): Entity traffic half metrics.
        calculation_version (str): Calculation rule version."""
    signals: list[SignalCandidate] = []
    for metric in metrics:
        first_traffic = metric['first_traffic']
        second_traffic = metric['second_traffic']
        growth_rate = divide_values(second_traffic - first_traffic, first_traffic)
        signal_type = None
        if first_traffic == 0 and second_traffic > 0:
            signal_type = 'new_activity'
        elif growth_rate >= 0.25:
            signal_type = 'growth_acceleration'
        elif growth_rate <= -0.20:
            signal_type = 'traffic_decline'
        if signal_type is None:
            continue
        severity = 'medium' if signal_type == 'new_activity' else classify_severity(growth_rate)
        signals.append(
            SignalCandidate(
                signal_type=signal_type,
                signal_group='growth',
                entity_type=metric['entity_type'],
                entity_id=metric['entity_id'],
                country_id=metric.get('country_id'),
                company_id=metric.get('company_id'),
                domain_id=metric.get('domain_id'),
                date_from=metric['date_from'],
                date_to=metric['date_to'],
                severity=severity,
                value=float(second_traffic),
                baseline_value=float(first_traffic),
                delta_value=float(second_traffic - first_traffic),
                delta_percent=growth_rate,
                message=f"{metric['entity_label']} shows {signal_type.replace('_', ' ')} in the selected period.",
                details={
                    'first_half_traffic': first_traffic,
                    'second_half_traffic': second_traffic,
                    'growth_rate': growth_rate,
                },
                calculation_version=calculation_version,
            )
        )
    return signals


def build_country_signals(
    metrics: list[dict[str, Any]],
    calculation_version: str,
) -> list[SignalCandidate]:
    """Build country market signals.
    Args:
        metrics (list[dict[str, Any]]): Country market metrics.
        calculation_version (str): Calculation rule version."""
    signals: list[SignalCandidate] = []
    for metric in metrics:
        daily_values = metric['daily_traffic']
        mean_traffic = divide_values(sum(daily_values), len(daily_values)) if daily_values else 0.0
        volatility = divide_values(pstdev(daily_values), mean_traffic) if len(daily_values) > 1 else 0.0
        growth_rate = divide_values(
            metric['second_traffic'] - metric['first_traffic'],
            metric['first_traffic'],
        )
        common = {
            'entity_type': 'country',
            'entity_id': str(metric['country_id']),
            'country_id': metric['country_id'],
            'date_from': metric['date_from'],
            'date_to': metric['date_to'],
            'calculation_version': calculation_version,
        }
        concentration_details = {
            'total_traffic': metric['total_traffic'],
            'top1_share': metric['top1_share'],
            'top3_share': metric['top3_share'],
            'active_competitors': metric['active_competitors'],
            'growth_rate': growth_rate,
        }
        if volatility >= 0.35:
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='high_volatility',
                    signal_group='volatility',
                    severity=classify_severity(volatility),
                    value=volatility,
                    baseline_value=mean_traffic,
                    message=f"{metric['country']} has high daily traffic volatility.",
                    details={'volatility': volatility, 'mean_daily_traffic': mean_traffic},
                )
            )
        elif daily_values and volatility <= 0.10:
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='stable_market',
                    signal_group='volatility',
                    severity='low',
                    value=volatility,
                    baseline_value=mean_traffic,
                    message=f"{metric['country']} has a stable daily traffic pattern.",
                    details={'volatility': volatility, 'mean_daily_traffic': mean_traffic},
                )
            )
        if metric['top1_share'] >= 0.50 or metric['top3_share'] >= 0.80:
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='high_concentration',
                    signal_group='competition',
                    severity='high' if metric['top1_share'] >= 0.65 else 'medium',
                    value=metric['top1_share'],
                    message=f"{metric['country']} traffic is concentrated among leading companies.",
                    details=concentration_details,
                )
            )
        if metric['active_competitors'] <= 3 and metric['total_traffic'] >= MIN_MARKET_TRAFFIC:
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='low_competitive_noise',
                    signal_group='competition',
                    severity='medium',
                    value=float(metric['active_competitors']),
                    message=f"{metric['country']} has a limited number of active competitors.",
                    details=concentration_details,
                )
            )
        if metric['top1_share'] < 0.25 and metric['active_competitors'] >= 8:
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='fragmented_market',
                    signal_group='competition',
                    severity='medium',
                    value=metric['top1_share'],
                    message=f"{metric['country']} has a fragmented competitive structure.",
                    details=concentration_details,
                )
            )
        if growth_rate >= 0.20 and metric['top1_share'] >= 0.50:
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='overheated_market',
                    signal_group='competition',
                    severity='high' if growth_rate >= 0.50 else 'medium',
                    value=growth_rate,
                    baseline_value=metric['top1_share'],
                    message=f"{metric['country']} combines strong growth with high competitor concentration.",
                    details=concentration_details,
                )
            )
        if (
            metric['active_competitors'] <= 3
            and metric['total_traffic'] >= MIN_MARKET_TRAFFIC
            and growth_rate >= 0
        ):
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='low_noise_market',
                    signal_group='territory',
                    severity='medium',
                    value=float(metric['total_traffic']),
                    delta_percent=growth_rate,
                    message=f"{metric['country']} combines positive traffic movement with low competitive noise.",
                    details=concentration_details,
                )
            )
        if metric['first_traffic'] == 0 and metric['second_traffic'] >= MIN_MARKET_TRAFFIC:
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='new_territory',
                    signal_group='territory',
                    severity='medium',
                    value=float(metric['second_traffic']),
                    baseline_value=0.0,
                    message=f"{metric['country']} shows meaningful new traffic activity.",
                    details=concentration_details,
                )
            )
        if (
            metric['first_traffic'] >= MIN_MARKET_TRAFFIC
            and metric['second_traffic'] <= metric['first_traffic'] * 0.10
        ):
            signals.append(
                SignalCandidate(
                    **common,
                    signal_type='forgotten_territory',
                    signal_group='territory',
                    severity='high',
                    value=float(metric['second_traffic']),
                    baseline_value=float(metric['first_traffic']),
                    delta_percent=growth_rate,
                    message=f"{metric['country']} traffic has fallen close to inactivity.",
                    details=concentration_details,
                )
            )
    return signals


def build_channel_signals(
    metrics: list[dict[str, Any]],
    calculation_version: str,
) -> list[SignalCandidate]:
    """Build channel shift signals.
    Args:
        metrics (list[dict[str, Any]]): Channel share half metrics.
        calculation_version (str): Calculation rule version."""
    signals: list[SignalCandidate] = []
    for metric in metrics:
        share_delta = metric['second_share'] - metric['first_share']
        if abs(share_delta) < 0.20:
            continue
        signals.append(
            SignalCandidate(
                signal_type='channel_shift',
                signal_group='channel',
                entity_type='channel',
                entity_id=metric['channel'],
                date_from=metric['date_from'],
                date_to=metric['date_to'],
                severity=classify_severity(share_delta),
                value=metric['second_share'],
                baseline_value=metric['first_share'],
                delta_value=share_delta,
                delta_percent=share_delta,
                message=f"{metric['channel'].title()} traffic share shifted materially between period halves.",
                details={
                    'channel': metric['channel'],
                    'shift_type': f"{metric['channel']}_shift",
                    'first_half_share': metric['first_share'],
                    'second_half_share': metric['second_share'],
                    'share_delta': share_delta,
                },
                calculation_version=calculation_version,
            )
        )
    return signals


def build_expansion_signals(
    metrics: list[dict[str, Any]],
    calculation_version: str,
) -> list[SignalCandidate]:
    """Build competitor expansion signals.
    Args:
        metrics (list[dict[str, Any]]): Company expansion metrics.
        calculation_version (str): Calculation rule version."""
    signals: list[SignalCandidate] = []
    for metric in metrics:
        growth_rate = divide_values(
            metric['second_traffic'] - metric['first_traffic'],
            metric['first_traffic'],
        )
        if metric['new_countries_count'] < 2 or growth_rate <= 0.20:
            continue
        signals.append(
            SignalCandidate(
                signal_type='competitor_expansion',
                signal_group='competition',
                entity_type='company',
                entity_id=str(metric['company_id']),
                company_id=metric['company_id'],
                date_from=metric['date_from'],
                date_to=metric['date_to'],
                severity=classify_severity(growth_rate),
                value=float(metric['new_countries_count']),
                baseline_value=float(metric['first_traffic']),
                delta_value=float(metric['second_traffic'] - metric['first_traffic']),
                delta_percent=growth_rate,
                message=f"{metric['company']} expanded into multiple active territories with traffic growth.",
                details={
                    'first_half_traffic': metric['first_traffic'],
                    'second_half_traffic': metric['second_traffic'],
                    'growth_rate': growth_rate,
                    'new_countries_count': metric['new_countries_count'],
                    'new_country_ids': metric['new_country_ids'],
                },
                calculation_version=calculation_version,
            )
        )
    return signals


def build_quality_signals(
    metric: dict[str, Any],
    calculation_version: str,
) -> list[SignalCandidate]:
    """Build traffic quality signals.
    Args:
        metric (dict[str, Any]): Period quality half metrics.
        calculation_version (str): Calculation rule version."""
    bounce_delta = metric['second_bounce_rate'] - metric['first_bounce_rate']
    duration_delta = divide_values(
        metric['second_duration'] - metric['first_duration'],
        metric['first_duration'],
    )
    if bounce_delta < 0.10 and duration_delta > -0.20:
        return []
    severity = 'high' if bounce_delta >= 0.20 or duration_delta <= -0.40 else 'medium'
    signal = SignalCandidate(
        signal_type='traffic_quality_degradation',
        signal_group='quality',
        entity_type='market',
        entity_id='selected_scope',
        date_from=metric['date_from'],
        date_to=metric['date_to'],
        severity=severity,
        value=metric['second_bounce_rate'],
        baseline_value=metric['first_bounce_rate'],
        delta_value=bounce_delta,
        delta_percent=duration_delta,
        message='Traffic engagement quality weakened between the first and second period halves.',
        details={
            'first_half_bounce_rate': metric['first_bounce_rate'],
            'second_half_bounce_rate': metric['second_bounce_rate'],
            'bounce_rate_delta': bounce_delta,
            'first_half_duration': metric['first_duration'],
            'second_half_duration': metric['second_duration'],
            'duration_delta_percent': duration_delta,
        },
        calculation_version=calculation_version,
    )
    return [signal]
