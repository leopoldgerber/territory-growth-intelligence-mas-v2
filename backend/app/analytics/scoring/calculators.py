from datetime import date
from math import log1p
from typing import Any

from app.analytics.country_intelligence import divide_values
from app.analytics.scoring.schemas import CountryMetric, FactorResult, ScoreCandidate

RECOMMENDED_WEIGHTS = {
    'market_size': 0.18,
    'growth': 0.18,
    'traffic_quality': 0.16,
    'competition_level': 0.14,
    'concentration': 0.12,
    'channel_stability': 0.10,
    'entry_risk': 0.10,
    'position_potential': 0.12,
}
WEIGHT_TOTAL = sum(RECOMMENDED_WEIGHTS.values())
FACTOR_WEIGHTS = {factor: weight / WEIGHT_TOTAL for factor, weight in RECOMMENDED_WEIGHTS.items()}
RISK_SIGNALS = {
    'high_concentration',
    'overheated_market',
    'traffic_quality_degradation',
    'high_volatility',
    'forgotten_territory',
    'mobile_growth_low_quality',
}
POSITIVE_SIGNALS = {
    'growth_acceleration',
    'low_competitive_noise',
    'fragmented_market',
    'new_territory',
    'stable_market',
    'small_but_growing',
}
FACTOR_LABELS = {
    'market_size': ('Strong market size', 'Weak market size'),
    'growth': ('Healthy growth', 'Negative growth'),
    'traffic_quality': ('Good traffic quality', 'Weak traffic quality'),
    'competition_level': ('Balanced competitive environment', 'High competitive pressure'),
    'concentration': ('Low competitor concentration', 'High competitor concentration'),
    'channel_stability': ('Stable channels', 'Unstable channel mix'),
    'entry_risk': ('Low entry risk', 'Elevated entry risk'),
    'position_potential': ('Strong position potential', 'Weak position potential'),
}


def clamp_score(value: float) -> float:
    """Clamp score to the supported range.
    Args:
        value (float): Source score."""
    return min(max(value, 0.0), 100.0)


def factor_status(score: float, available: bool = True) -> str:
    """Classify one factor score.
    Args:
        score (float): Normalized factor score.
        available (bool): Whether the underlying data is available."""
    if not available:
        return 'not_available'
    if score >= 75:
        return 'strong'
    if score <= 40:
        return 'weak'
    return 'moderate'


def build_factor(
    factor: str,
    raw_value: Any,
    score: float,
    explanation: str,
    available: bool = True,
) -> FactorResult:
    """Build an explainable factor result.
    Args:
        factor (str): Factor identifier.
        raw_value (Any): Source metric value.
        score (float): Normalized factor score.
        explanation (str): Human-readable factor explanation.
        available (bool): Whether the underlying data is available."""
    normalized_score = round(clamp_score(score), 4)
    weight = FACTOR_WEIGHTS[factor]
    return FactorResult(
        factor=factor,
        raw_value=raw_value,
        score=normalized_score,
        weight=weight,
        weighted_score=round(normalized_score * weight, 4),
        status=factor_status(normalized_score, available),
        explanation=explanation,
    )


def score_market_size(metric: CountryMetric, percentile: float, single_country: bool) -> FactorResult:
    """Score country market size.
    Args:
        metric (CountryMetric): Country-level source metrics.
        percentile (float): Traffic percentile among scored countries.
        single_country (bool): Whether only one country is scored."""
    if single_country:
        reference_traffic = max(metric.total_traffic, 10_000_000)
        score = divide_values(log1p(metric.total_traffic), log1p(reference_traffic)) * 100
        explanation = f'{metric.country} uses the single-country logarithmic traffic fallback.'
    else:
        score = percentile * 100
        explanation = f'{metric.country} is at the {score:.1f} traffic percentile in the selected scope.'
    return build_factor('market_size', metric.total_traffic, score, explanation)


def score_growth(metric: CountryMetric) -> FactorResult:
    """Score country traffic growth.
    Args:
        metric (CountryMetric): Country-level source metrics."""
    if metric.first_traffic == 0 and metric.second_traffic > 0:
        return build_factor(
            'growth',
            None,
            75,
            'Traffic appears in the second half of the selected period.',
        )
    growth_rate = divide_values(metric.second_traffic - metric.first_traffic, metric.first_traffic)
    if growth_rate >= 0.50:
        score = 100
    elif growth_rate >= 0.25:
        score = 80
    elif growth_rate >= 0.10:
        score = 65
    elif growth_rate >= -0.05:
        score = 50
    elif growth_rate > -0.20:
        score = 35
    elif growth_rate > -0.50:
        score = 20
    else:
        score = 0
    explanation = f'Traffic changed by {growth_rate:.1%} between period halves.'
    return build_factor('growth', growth_rate, score, explanation)


def score_quality(metric: CountryMetric) -> FactorResult:
    """Score country traffic quality.
    Args:
        metric (CountryMetric): Country-level source metrics."""
    duration_score = min(max(metric.avg_visit_duration, 0.0) / 180.0, 1.0) * 100
    no_bounce_score = min(max(1.0 - metric.bounce_rate, 0.0), 1.0) * 100
    pages_score = min(max(metric.pages_per_visit, 0.0) / 5.0, 1.0) * 100
    score = duration_score * 0.35 + no_bounce_score * 0.45 + pages_score * 0.20
    raw_value = {
        'bounce_rate': metric.bounce_rate,
        'avg_visit_duration': metric.avg_visit_duration,
        'pages_per_visit': metric.pages_per_visit,
    }
    explanation = (
        f'Quality combines {metric.avg_visit_duration:.1f}s duration, '
        f'{metric.bounce_rate:.1%} bounce rate, and {metric.pages_per_visit:.2f} pages per visit.'
    )
    return build_factor('traffic_quality', raw_value, score, explanation)


def score_competition(metric: CountryMetric, market_size_score: float) -> FactorResult:
    """Score country competition level.
    Args:
        metric (CountryMetric): Country-level source metrics.
        market_size_score (float): Normalized market size score."""
    if metric.active_companies <= 2:
        score = 75
    elif metric.active_companies <= 5:
        score = 90
    elif metric.active_companies <= 10:
        score = 70
    elif metric.active_companies <= 20:
        score = 50
    else:
        score = 30
    if market_size_score < 20:
        score -= 20
    explanation = (
        f'{metric.active_companies} active companies and {metric.active_domains} active domains '
        'define the competitive density.'
    )
    return build_factor('competition_level', metric.active_companies, score, explanation)


def score_concentration(metric: CountryMetric) -> FactorResult:
    """Score competitor concentration.
    Args:
        metric (CountryMetric): Country-level source metrics."""
    if metric.top1_share >= 0.50 or metric.top3_share >= 0.80:
        score = 25
    elif metric.top1_share < 0.25 and metric.top3_share < 0.60:
        score = 90
    elif metric.top1_share < 0.40 and metric.top3_share < 0.75:
        score = 70
    elif metric.top1_share < 0.50:
        score = 50
    else:
        score = 25
    raw_value = {'top1_share': metric.top1_share, 'top3_share': metric.top3_share}
    explanation = f'Top 1 holds {metric.top1_share:.1%}; top 3 hold {metric.top3_share:.1%}.'
    return build_factor('concentration', raw_value, score, explanation)


def score_channels(signals: list[dict[str, Any]]) -> FactorResult:
    """Score channel stability from derived signals.
    Args:
        signals (list[dict[str, Any]]): Applicable derived signals."""
    channel_shifts = [signal for signal in signals if signal['signal_type'] == 'channel_shift']
    if not signals:
        return build_factor(
            'channel_stability',
            None,
            50,
            'Derived signals are unavailable; a neutral fallback is used.',
            False,
        )
    high_count = sum(signal['severity'] in {'high', 'critical'} for signal in channel_shifts)
    medium_count = sum(signal['severity'] == 'medium' for signal in channel_shifts)
    if high_count > 1:
        score = 20
    elif high_count == 1:
        score = 35
    elif medium_count > 0:
        score = 60
    else:
        score = 80
    explanation = f'{len(channel_shifts)} channel shift signals are present in the selected scope.'
    return build_factor('channel_stability', len(channel_shifts), score, explanation)


def score_entry_risk(signals: list[dict[str, Any]]) -> FactorResult:
    """Score inverted entry risk.
    Args:
        signals (list[dict[str, Any]]): Applicable derived signals."""
    risks = [signal for signal in signals if signal['signal_type'] in RISK_SIGNALS]
    penalties = {'critical': 25, 'high': 25, 'medium': 15, 'low': 5}
    penalty = sum(penalties.get(signal['severity'], 0) for signal in risks)
    explanation = f'{len(risks)} risk signals produce a {penalty}-point penalty.'
    return build_factor('entry_risk', [signal['signal_type'] for signal in risks], 100 - penalty, explanation)


def score_position(signals: list[dict[str, Any]]) -> FactorResult:
    """Score position potential.
    Args:
        signals (list[dict[str, Any]]): Applicable derived signals."""
    positives = [signal for signal in signals if signal['signal_type'] in POSITIVE_SIGNALS]
    bonuses = {'critical': 20, 'high': 20, 'medium': 12, 'low': 5}
    bonus = sum(bonuses.get(signal['severity'], 0) for signal in positives)
    explanation = f'{len(positives)} positive signals produce a {bonus}-point bonus.'
    return build_factor(
        'position_potential',
        [signal['signal_type'] for signal in positives],
        50 + bonus,
        explanation,
    )


def score_category(score: float) -> str:
    """Classify final opportunity score.
    Args:
        score (float): Final normalized score."""
    if score >= 80:
        return 'very_high'
    if score >= 65:
        return 'high'
    if score >= 50:
        return 'medium'
    if score >= 35:
        return 'low'
    return 'very_low'


def build_candidate(
    metric: CountryMetric,
    percentile: float,
    single_country: bool,
    signals: list[dict[str, Any]],
    scope: str,
    date_from: date,
    date_to: date,
    calculation_version: str,
) -> ScoreCandidate:
    """Build one explainable opportunity score.
    Args:
        metric (CountryMetric): Country-level source metrics.
        percentile (float): Traffic percentile among scored countries.
        single_country (bool): Whether only one country is scored.
        signals (list[dict[str, Any]]): Applicable derived signals.
        scope (str): Analytical scope.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date.
        calculation_version (str): Calculation version."""
    market_size = score_market_size(metric, percentile, single_country)
    factors = [
        market_size,
        score_growth(metric),
        score_quality(metric),
        score_competition(metric, market_size.score),
        score_concentration(metric),
        score_channels(signals),
        score_entry_risk(signals),
        score_position(signals),
    ]
    total_score = round(sum(factor.weighted_score for factor in factors), 4)
    strengths = [FACTOR_LABELS[factor.factor][0] for factor in factors if factor.score >= 75]
    weaknesses = [FACTOR_LABELS[factor.factor][1] for factor in factors if factor.score <= 40]
    risks = [
        signal['signal_type'].replace('_', ' ').title()
        for signal in signals
        if signal['signal_type'] in RISK_SIGNALS
    ]
    positive_factors = [factor.factor for factor in sorted(factors, key=lambda item: item.score, reverse=True)[:2]]
    negative_factors = [factor.factor for factor in sorted(factors, key=lambda item: item.score)[:2]]
    category = score_category(total_score)
    category_label = category.replace('_', ' ')
    explanation = {
        'summary': (
            f'{metric.country} has a {category_label} opportunity score based on selected metrics.'
        ),
        'factor_breakdown': [factor.model_dump() for factor in factors],
        'top_positive_factors': positive_factors,
        'top_negative_factors': negative_factors,
        'signals_used': sorted({signal['signal_type'] for signal in signals}),
        'fallbacks_used': [factor.factor for factor in factors if factor.status == 'not_available'],
    }
    return ScoreCandidate(
        country_id=metric.country_id,
        country=metric.country,
        country_code=metric.country_code,
        scope=scope,
        date_from=date_from,
        date_to=date_to,
        opportunity_score=total_score,
        score_category=category,
        factors=factors,
        strengths=strengths,
        weaknesses=weaknesses,
        risks=risks,
        explanation=explanation,
        details={'total_traffic': metric.total_traffic, 'signals_available': bool(signals)},
        calculation_version=calculation_version,
    )
