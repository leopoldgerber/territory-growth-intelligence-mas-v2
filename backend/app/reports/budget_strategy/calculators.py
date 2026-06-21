from decimal import Decimal

from app.reports.budget_strategy.schemas import (
    AllocationResult,
    BudgetAllocationItem,
    BudgetChannelRole,
    ChannelInput,
    ExpectedEffect,
    StrategyRisk,
)

CHANNEL_LABELS = {
    'search': 'SEO / Search',
    'paid': 'Paid',
    'referral': 'Referral / Partnerships',
    'social': 'Social',
    'direct': 'Brand / Direct',
}
ROLE_LIMITS = {
    'priority': (0.25, 0.45),
    'test': (0.05, 0.15),
    'supporting': (0.05, 0.20),
    'risky': (0.00, 0.10),
}


def clamp_value(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value.
    Args:
        value (float): Source value.
        minimum (float): Minimum allowed value.
        maximum (float): Maximum allowed value."""
    return min(max(value, minimum), maximum)


def score_channel(data: ChannelInput) -> float:
    """Calculate channel opportunity score.
    Args:
        data (ChannelInput): Normalized channel inputs."""
    market_signal = clamp_value(data.market_share * 160, 20, 100)
    competitor_gap = clamp_value(50 + (data.market_share - data.competitor_share) * 100, 0, 100)
    score = (
        market_signal * 0.30
        + competitor_gap * 0.20
        + data.quality_score * 0.20
        + data.stability_score * 0.15
        + data.opportunity_modifier * 0.15
    )
    if data.high_risk:
        score -= 20
    return round(clamp_value(score, 0, 100), 4)


def assign_roles(scores: dict[str, float], risks: set[str]) -> dict[str, BudgetChannelRole]:
    """Assign channel strategy roles.
    Args:
        scores (dict[str, float]): Channel opportunity scores.
        risks (set[str]): Channels with elevated risk."""
    ordered = sorted(scores, key=scores.get, reverse=True)
    priority_channels = [
        channel for channel in ordered if channel not in risks and scores[channel] >= 35
    ][:2]
    roles: dict[str, BudgetChannelRole] = {}
    for channel in ordered:
        score = scores[channel]
        if channel in risks or score < 35:
            roles[channel] = 'risky'
        elif channel in priority_channels:
            roles[channel] = 'priority'
        elif score >= 50:
            roles[channel] = 'supporting'
        else:
            roles[channel] = 'test'
    return roles


def active_channels(
    budget_amount: Decimal,
    scores: dict[str, float],
    roles: dict[str, BudgetChannelRole],
) -> list[str]:
    """Select active channels for available budget.
    Args:
        budget_amount (Decimal): Total strategy budget.
        scores (dict[str, float]): Channel opportunity scores.
        roles (dict[str, BudgetChannelRole]): Assigned channel roles."""
    maximum_channels = 3 if budget_amount < 10_000 else 4 if budget_amount < 50_000 else 5
    ordered = sorted(scores, key=scores.get, reverse=True)
    priority = [channel for channel in ordered if roles[channel] == 'priority']
    remaining = [channel for channel in ordered if roles[channel] != 'priority']
    return (priority + remaining)[:maximum_channels]


def allocate_shares(
    active: list[str],
    scores: dict[str, float],
    roles: dict[str, BudgetChannelRole],
) -> dict[str, float]:
    """Allocate guarded budget shares.
    Args:
        active (list[str]): Active budget channels.
        scores (dict[str, float]): Channel opportunity scores.
        roles (dict[str, BudgetChannelRole]): Assigned channel roles."""
    total_score = sum(max(scores[channel], 1) for channel in active)
    shares = {
        channel: clamp_value(
            max(scores[channel], 1) / total_score,
            ROLE_LIMITS[roles[channel]][0],
            ROLE_LIMITS[roles[channel]][1],
        )
        for channel in active
    }
    for _iteration in range(10):
        difference = 1.0 - sum(shares.values())
        if abs(difference) < 0.000001:
            break
        adjustable = [
            channel
            for channel in active
            if (difference > 0 and shares[channel] < ROLE_LIMITS[roles[channel]][1])
            or (difference < 0 and shares[channel] > ROLE_LIMITS[roles[channel]][0])
        ]
        if not adjustable:
            break
        adjustment = difference / len(adjustable)
        for channel in adjustable:
            minimum, maximum = ROLE_LIMITS[roles[channel]]
            shares[channel] = clamp_value(shares[channel] + adjustment, minimum, maximum)
    difference = 1.0 - sum(shares.values())
    if abs(difference) >= 0.000001:
        for channel in active:
            minimum, maximum = ROLE_LIMITS[roles[channel]]
            adjusted = clamp_value(shares[channel] + difference, minimum, maximum)
            difference -= adjusted - shares[channel]
            shares[channel] = adjusted
            if abs(difference) < 0.000001:
                break
    return shares


def build_risks(signal_types: list[str], score_risks: list[str]) -> list[StrategyRisk]:
    """Build explainable strategy risks.
    Args:
        signal_types (list[str]): Applicable derived signal types.
        score_risks (list[str]): Opportunity scoring risks."""
    definitions = {
        'high_concentration': ('high_competitor_concentration', 'high', ['paid', 'direct']),
        'overheated_market': ('overheated_market', 'high', ['paid', 'search']),
        'channel_shift': ('channel_instability', 'medium', list(CHANNEL_LABELS)),
        'traffic_quality_degradation': ('traffic_quality_degradation', 'high', ['paid', 'social']),
        'mobile_growth_low_quality': ('mobile_quality_gap', 'medium', ['paid', 'social']),
        'high_volatility': ('high_volatility', 'high', list(CHANNEL_LABELS)),
    }
    risks: list[StrategyRisk] = []
    for signal in sorted(set(signal_types)):
        if signal not in definitions:
            continue
        risk_type, severity, channels = definitions[signal]
        signal_label = signal.replace('_', ' ').title()
        risks.append(
            StrategyRisk(
                type=risk_type,
                severity=severity,
                message=f'{signal_label} is present in the source analytics.',
                affected_channels=channels,
                mitigation_hint='Keep allocation controlled and validate traffic quality before scaling.',
            )
        )
    if any('concentration' in risk.lower() for risk in score_risks) and not any(
        risk.type == 'high_competitor_concentration' for risk in risks
    ):
        risks.append(
            StrategyRisk(
                type='high_competitor_concentration',
                severity='medium',
                message='Opportunity scoring identifies competitor concentration risk.',
                affected_channels=['paid', 'direct'],
                mitigation_hint='Use diversified tests instead of concentrating spend in one channel.',
            )
        )
    return risks


def build_allocation(
    channels: list[ChannelInput],
    budget_amount: Decimal,
    signal_types: list[str],
    score_risks: list[str],
) -> AllocationResult:
    """Build complete budget allocation strategy.
    Args:
        channels (list[ChannelInput]): Normalized channel inputs.
        budget_amount (Decimal): Total budget amount.
        signal_types (list[str]): Applicable signal types.
        score_risks (list[str]): Opportunity scoring risks."""
    scores = {channel.channel: score_channel(channel) for channel in channels}
    risks = build_risks(signal_types, score_risks)
    risky_channels = {channel.channel for channel in channels if channel.high_risk}
    roles = assign_roles(scores, risky_channels)
    active = active_channels(budget_amount, scores, roles)
    shares = allocate_shares(active, scores, roles)
    total_amount = round(float(budget_amount), 2)
    allocation: list[BudgetAllocationItem] = []
    allocated_amount = 0.0
    for index, channel in enumerate(active):
        amount = (
            round(total_amount - allocated_amount, 2)
            if index == len(active) - 1
            else round(total_amount * shares[channel], 2)
        )
        allocated_amount += amount
        allocation.append(
            BudgetAllocationItem(
                channel=channel,
                role=roles[channel],
                amount=amount,
                share=round(amount / total_amount, 6),
                score=scores[channel],
                reason=(
                    f'{CHANNEL_LABELS[channel]} received a {roles[channel]} role from normalized '
                    'market, quality, stability, and opportunity signals.'
                ),
            )
        )
    role_groups = {
        role: [channel for channel in active if roles[channel] == role]
        for role in ROLE_LIMITS
    }
    priority = [CHANNEL_LABELS[item.channel] for item in allocation if item.role == 'priority']
    tests = [CHANNEL_LABELS[item.channel] for item in allocation if item.role == 'test']
    confidence = 'low' if not signal_types else 'medium' if risks else 'high'
    expected_effect = ExpectedEffect(
        confidence=confidence,
        expected_direction='balanced_growth',
        primary_effects=[f'Increase {channel} acquisition potential' for channel in priority]
        or ['Validate market response'],
        secondary_effects=[f'Test {channel} without overexposure' for channel in tests],
        measurement_focus=['traffic quality', 'bounce rate', 'desktop/mobile split', 'channel share changes'],
    )
    primary_focus = ', '.join(priority) if priority else 'controlled channel tests'
    recommended = (
        f'Use a balanced strategy led by {primary_focus}. '
        'Keep test and risky allocations capped, and validate traffic quality and channel share movement '
        'before scaling.'
    )
    return AllocationResult(
        allocation=allocation,
        channel_roles=role_groups,
        expected_effect=expected_effect,
        risks=risks,
        explanation={'channel_scores': scores, 'guardrails': ROLE_LIMITS, 'active_channels': active},
        recommended_approach=recommended,
    )
