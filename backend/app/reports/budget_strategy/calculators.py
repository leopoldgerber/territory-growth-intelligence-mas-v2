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
PAID_WEAK_THRESHOLD = 0.05
PAID_LOCAL_ZERO_THRESHOLD = 0.0
SMALL_BUDGET_THRESHOLD = Decimal('10000')
ROLE_LIMITS = {
    'priority': (0.25, 0.45),
    'test': (0.05, 0.15),
    'supporting': (0.05, 0.20),
    'risky': (0.00, 0.10),
}
ENTRY_ROLE_LIMITS = {
    'priority': (0.25, 0.40),
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


def score_entry_channel(data: ChannelInput) -> float:
    """Calculate market entry channel score.
    Args:
        data (ChannelInput): Normalized channel inputs."""
    local_signal = clamp_value(data.market_share * 170, 0, 100)
    company_signal = clamp_value(data.company_global_share * 170, 0, 100)
    entry_fit = 85.0
    if data.channel == 'direct':
        entry_fit = 35.0
    elif data.channel == 'paid':
        entry_fit = 45.0 if data.market_share <= 0.01 and data.company_global_share <= 0.05 else 65.0
    elif data.channel == 'search':
        entry_fit = 95.0
    elif data.channel in {'referral', 'social'}:
        entry_fit = 70.0
    score = (
        local_signal * 0.35
        + company_signal * 0.30
        + entry_fit * 0.15
        + data.quality_score * 0.10
        + data.opportunity_modifier * 0.10
    )
    if data.high_risk:
        score -= 25
    if is_paid_unsupported(data):
        score -= 20
    return round(clamp_value(score, 0, 100), 4)


def classify_strength(value: float) -> str:
    """Classify channel evidence strength.
    Args:
        value (float): Channel share value."""
    if value >= 0.25:
        return 'strong'
    if value >= 0.05:
        return 'proven'
    if value > 0:
        return 'weak'
    return 'absent'


def is_paid_unsupported(data: ChannelInput) -> bool:
    """Check unsupported paid evidence.
    Args:
        data (ChannelInput): Normalized channel inputs."""
    return (
        data.channel == 'paid'
        and data.market_share <= PAID_LOCAL_ZERO_THRESHOLD
        and data.company_global_share < PAID_WEAK_THRESHOLD
    )


def build_channel_limits(
    channels: list[ChannelInput],
    budget_amount: Decimal,
    market_entry: bool,
) -> dict[str, tuple[float, float]]:
    """Build channel-specific budget limits.
    Args:
        channels (list[ChannelInput]): Normalized channel inputs.
        budget_amount (Decimal): Total strategy budget.
        market_entry (bool): Whether strategy is market entry."""
    if not market_entry:
        return {}
    limits: dict[str, tuple[float, float]] = {}
    paid_cap = 0.05 if budget_amount < SMALL_BUDGET_THRESHOLD else 0.10
    for data in channels:
        if is_paid_unsupported(data):
            limits[data.channel] = (0.0, paid_cap)
    return limits


def assign_entry_roles(
    channels: list[ChannelInput],
    scores: dict[str, float],
    risks: set[str],
    company_has_country_data: bool,
) -> dict[str, BudgetChannelRole]:
    """Assign market entry channel roles.
    Args:
        channels (list[ChannelInput]): Normalized channel inputs.
        scores (dict[str, float]): Channel opportunity scores.
        risks (set[str]): Channels with elevated risk.
        company_has_country_data (bool): Whether target company has country data."""
    roles: dict[str, BudgetChannelRole] = {}
    priority_limit = 2 if company_has_country_data else 1
    priority_candidates: list[str] = []
    for data in channels:
        local_strength = classify_strength(data.market_share)
        company_strength = classify_strength(data.company_global_share)
        if data.channel in risks:
            roles[data.channel] = 'risky'
        elif data.channel == 'direct':
            roles[data.channel] = 'supporting' if local_strength in {'strong', 'proven'} else 'test'
        elif is_paid_unsupported(data):
            roles[data.channel] = 'test'
        elif local_strength in {'strong', 'proven'} and company_strength in {'strong', 'proven'}:
            roles[data.channel] = 'priority'
            priority_candidates.append(data.channel)
        elif local_strength in {'strong', 'proven'} or company_strength in {'strong', 'proven'}:
            roles[data.channel] = 'test' if data.channel in {'paid', 'social'} else 'supporting'
        elif local_strength == 'weak' or company_strength == 'weak':
            roles[data.channel] = 'test'
        else:
            roles[data.channel] = 'risky'
    priority_candidates.sort(key=lambda channel: scores[channel], reverse=True)
    allowed_priorities = set(priority_candidates[:priority_limit])
    for channel, role in list(roles.items()):
        if role == 'priority' and channel not in allowed_priorities:
            roles[channel] = 'supporting' if channel in {'search', 'referral', 'direct'} else 'test'
    return roles


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


def expand_entry_channels(
    active: list[str],
    scores: dict[str, float],
    channel_limits: dict[str, tuple[float, float]],
) -> list[str]:
    """Expand market entry channels for hard caps.
    Args:
        active (list[str]): Initially active budget channels.
        scores (dict[str, float]): Channel opportunity scores.
        channel_limits (dict[str, tuple[float, float]]): Channel-specific hard limits."""
    if not channel_limits:
        return active
    expanded = list(active)
    for channel in sorted(scores, key=scores.get, reverse=True):
        if channel not in expanded:
            expanded.append(channel)
    return expanded


def allocate_shares(
    active: list[str],
    scores: dict[str, float],
    roles: dict[str, BudgetChannelRole],
    role_limits: dict[str, tuple[float, float]] | None = None,
    channel_limits: dict[str, tuple[float, float]] | None = None,
) -> dict[str, float]:
    """Allocate guarded budget shares.
    Args:
        active (list[str]): Active budget channels.
        scores (dict[str, float]): Channel opportunity scores.
        roles (dict[str, BudgetChannelRole]): Assigned channel roles.
        role_limits (dict[str, tuple[float, float]] | None): Budget share limits.
        channel_limits (dict[str, tuple[float, float]] | None): Channel-specific hard limits."""
    limits = role_limits or ROLE_LIMITS
    hard_limits = channel_limits or {}
    total_score = sum(max(scores[channel], 1) for channel in active)
    shares = {
        channel: clamp_value(
            max(scores[channel], 1) / total_score,
            hard_limits.get(channel, limits[roles[channel]])[0],
            hard_limits.get(channel, limits[roles[channel]])[1],
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
            if (difference > 0 and shares[channel] < hard_limits.get(channel, limits[roles[channel]])[1])
            or (difference < 0 and shares[channel] > hard_limits.get(channel, limits[roles[channel]])[0])
        ]
        if not adjustable:
            break
        adjustment = difference / len(adjustable)
        for channel in adjustable:
            minimum, maximum = hard_limits.get(channel, limits[roles[channel]])
            shares[channel] = clamp_value(shares[channel] + adjustment, minimum, maximum)
    difference = 1.0 - sum(shares.values())
    if abs(difference) >= 0.000001:
        for channel in active:
            minimum, maximum = hard_limits.get(channel, limits[roles[channel]])
            adjusted = clamp_value(shares[channel] + difference, minimum, maximum)
            difference -= adjusted - shares[channel]
            shares[channel] = adjusted
            if abs(difference) < 0.000001:
                break
    difference = 1.0 - sum(shares.values())
    if difference > 0.000001:
        flexible = [
            channel for channel in active if channel not in hard_limits or shares[channel] < hard_limits[channel][1]
        ]
        for channel in flexible:
            maximum = hard_limits[channel][1] if channel in hard_limits else 1.0
            adjusted = clamp_value(shares[channel] + difference, 0.0, maximum)
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


def build_reason(data: ChannelInput, role: BudgetChannelRole, market_entry: bool) -> str:
    """Build channel role explanation.
    Args:
        data (ChannelInput): Normalized channel inputs.
        role (BudgetChannelRole): Assigned channel role.
        market_entry (bool): Whether strategy is market entry."""
    if not market_entry:
        return (
            f'{CHANNEL_LABELS[data.channel]} received a {role} role from normalized '
            'market, quality, stability, and opportunity signals.'
        )
    local_strength = classify_strength(data.market_share)
    company_strength = classify_strength(data.company_global_share)
    if data.channel == 'direct':
        return (
            'Brand / Direct is treated as support in Market Entry: local competitors may have brand demand, '
            'but a new entrant should not assume the same direct demand immediately.'
        )
    if is_paid_unsupported(data):
        return (
            'Paid is not supported by target-country competitor evidence and is not a proven global strength '
            'for the selected company. Keep it as a small controlled test or omit it until paid demand and '
            'traffic quality are validated.'
        )
    if role == 'priority':
        return (
            f'{CHANNEL_LABELS[data.channel]} is confirmed by target-country evidence '
            f'({local_strength}) and company global profile ({company_strength}).'
        )
    if role == 'supporting':
        return (
            f'{CHANNEL_LABELS[data.channel]} supports entry because either local evidence '
            f'({local_strength}) or company profile ({company_strength}) is present.'
        )
    if role == 'test':
        return (
            f'{CHANNEL_LABELS[data.channel]} should be tested with a capped budget because evidence is partial: '
            f'local={local_strength}, company={company_strength}.'
        )
    return (
        f'{CHANNEL_LABELS[data.channel]} is risky because both local and company evidence are weak '
        'or elevated risk signals are present.'
    )


def build_recommendation(primary_focus: str, market_entry: bool) -> str:
    """Build strategy recommendation text.
    Args:
        primary_focus (str): Primary channel focus text.
        market_entry (bool): Whether strategy is market entry."""
    if market_entry:
        return (
            f'Use a market-entry strategy led by {primary_focus}. '
            'Prioritize channels confirmed by both local competitor evidence and company global strengths. '
            'Keep Direct as brand support and use Paid only as a controlled test unless evidence improves.'
        )
    return (
        f'Use a balanced strategy led by {primary_focus}. '
        'Keep test and risky allocations capped, and validate traffic quality and channel share movement '
        'before scaling.'
    )


def build_allocation(
    channels: list[ChannelInput],
    budget_amount: Decimal,
    signal_types: list[str],
    score_risks: list[str],
    strategy_mode: str = 'existing_presence',
    company_has_country_data: bool = True,
) -> AllocationResult:
    """Build complete budget allocation strategy.
    Args:
        channels (list[ChannelInput]): Normalized channel inputs.
        budget_amount (Decimal): Total budget amount.
        signal_types (list[str]): Applicable signal types.
        score_risks (list[str]): Opportunity scoring risks.
        strategy_mode (str): Strategy mode.
        company_has_country_data (bool): Whether target company has country data."""
    market_entry = strategy_mode == 'market_entry'
    scores = {
        channel.channel: score_entry_channel(channel) if market_entry else score_channel(channel)
        for channel in channels
    }
    risks = build_risks(signal_types, score_risks)
    risky_channels = {channel.channel for channel in channels if channel.high_risk}
    roles = (
        assign_entry_roles(channels, scores, risky_channels, company_has_country_data)
        if market_entry
        else assign_roles(scores, risky_channels)
    )
    channel_limits = build_channel_limits(channels, budget_amount, market_entry)
    active = active_channels(budget_amount, scores, roles)
    if market_entry:
        active = expand_entry_channels(active, scores, channel_limits)
    shares = allocate_shares(
        active,
        scores,
        roles,
        ENTRY_ROLE_LIMITS if market_entry else ROLE_LIMITS,
        channel_limits,
    )
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
                reason=build_reason(next(item for item in channels if item.channel == channel), roles[channel], market_entry),
            )
        )
    role_groups = {
        role: [channel for channel in active if roles[channel] == role]
        for role in ROLE_LIMITS
    }
    priority = [CHANNEL_LABELS[item.channel] for item in allocation if item.role == 'priority']
    tests = [CHANNEL_LABELS[item.channel] for item in allocation if item.role == 'test']
    company_profile_available = any(channel.company_global_share > 0 for channel in channels)
    channel_data_available = any(channel.market_share > 0 for channel in channels)
    confidence = 'low' if not signal_types else 'medium' if risks else 'high'
    if market_entry:
        if not channel_data_available:
            confidence = 'low'
        elif not company_profile_available or risks:
            confidence = 'medium'
        else:
            confidence = 'high'
    expected_effect = ExpectedEffect(
        confidence=confidence,
        expected_direction='balanced_growth',
        primary_effects=[f'Increase {channel} acquisition potential' for channel in priority]
        or ['Validate market response'],
        secondary_effects=[f'Test {channel} without overexposure' for channel in tests],
        measurement_focus=['traffic quality', 'bounce rate', 'desktop/mobile split', 'channel share changes'],
    )
    primary_focus = ', '.join(priority) if priority else 'controlled channel tests'
    recommended = build_recommendation(primary_focus, market_entry)
    return AllocationResult(
        allocation=allocation,
        channel_roles=role_groups,
        expected_effect=expected_effect,
        risks=risks,
        explanation={
            'channel_scores': scores,
            'guardrails': ENTRY_ROLE_LIMITS if market_entry else ROLE_LIMITS,
            'active_channels': active,
            'company_global_shares': {channel.channel: channel.company_global_share for channel in channels},
        },
        recommended_approach=recommended,
    )
