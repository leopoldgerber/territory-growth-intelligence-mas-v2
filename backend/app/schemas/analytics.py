from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CountryIntelligenceFilters(BaseModel):
    project_id: UUID
    date_from: date | None
    date_to: date | None
    country: str
    tld: str
    company: str
    company_domain: str
    competitors: str
    competitor_domain: str


class FilterOption(BaseModel):
    label: str
    value: str


class DomainFilterOption(FilterOption):
    company_id: int
    tld: str | None


class AnalyticsFilterOptionsResponse(BaseModel):
    countries: list[FilterOption]
    tlds: list[FilterOption]
    companies: list[FilterOption]
    domains: list[DomainFilterOption]


class CountryIntelligenceSummary(BaseModel):
    total_traffic: int
    active_competitors: int
    active_domains: int
    country_count: int
    date_count: int


class TopCompetitor(BaseModel):
    company_id: int
    company: str
    traffic: int
    traffic_share: float
    domains_count: int


class TrafficTrendPoint(BaseModel):
    date: date
    traffic: int


class DeviceSplit(BaseModel):
    desktop_traffic: int
    mobile_traffic: int
    desktop_share: float
    mobile_share: float


class BounceSummary(BaseModel):
    no_bounce: int
    bounce: int
    bounce_rate: float


class EngagementMetrics(BaseModel):
    unique_visitors: int
    pages_per_visit: float
    avg_visit_duration: float


class MarketSignal(BaseModel):
    status: str
    growth_rate: float
    message: str


class CountryIntelligenceResponse(BaseModel):
    filters: CountryIntelligenceFilters
    selected_country_count: int
    summary: CountryIntelligenceSummary
    competitor_summary: CountryIntelligenceSummary
    top_competitors: list[TopCompetitor]
    traffic_trend: list[TrafficTrendPoint]
    competitor_traffic_trend: list[TrafficTrendPoint]
    device_split: DeviceSplit
    competitor_device_split: DeviceSplit
    bounce: BounceSummary
    competitor_bounce: BounceSummary
    engagement: EngagementMetrics
    competitor_engagement: EngagementMetrics
    market_signal: MarketSignal
    competitor_market_signal: MarketSignal


class CompetitorIntelligenceFilters(BaseModel):
    project_id: UUID
    date_from: date | None
    date_to: date | None
    competitors: str
    competitor_domain: str
    country: str
    tld: str


class CompetitorSummary(BaseModel):
    total_traffic: int
    active_countries: int
    active_domains: int
    top_country: str | None
    top_country_share: float
    growth_rate: float


class CompetitorCountryMetric(BaseModel):
    country_id: int
    country: str
    country_code: str
    traffic: int
    traffic_share: float
    growth_rate: float
    growth_status: str
    status: str


class CompetitorDependency(BaseModel):
    top1_country_share: float
    top3_country_share: float
    dependency_level: str


class PresenceStability(BaseModel):
    active_days: int
    period_days: int
    stability_rate: float
    status: str


class MarketWindow(BaseModel):
    country: str
    signal: str
    message: str


class CompetitorIntelligenceResponse(BaseModel):
    filters: CompetitorIntelligenceFilters
    summary: CompetitorSummary
    top_countries: list[CompetitorCountryMetric]
    growing_countries: list[CompetitorCountryMetric]
    declining_countries: list[CompetitorCountryMetric]
    anchor_markets: list[CompetitorCountryMetric]
    peripheral_markets: list[CompetitorCountryMetric]
    dependency: CompetitorDependency
    presence_stability: PresenceStability
    market_windows: list[MarketWindow]


class ChannelIntelligenceFilters(BaseModel):
    project_id: UUID
    date_from: date | None
    date_to: date | None
    country: str
    tld: str
    company: str
    company_domain: str
    competitors: str
    competitor_domain: str


class ChannelSummary(BaseModel):
    total_traffic: int
    dominant_channel: str | None
    dominant_channel_share: float
    paid_share: float
    organic_share: float
    competitors_count: int
    domains_count: int


class ChannelMixItem(BaseModel):
    channel: str
    traffic: int
    share: float


class CompetitorChannelDependency(BaseModel):
    company_id: int
    company: str
    total_traffic: int
    dominant_channel: str | None
    dominant_channel_share: float
    direct_share: float
    search_share: float
    paid_share: float
    referral_share: float
    social_share: float
    dependency_level: str


class ChannelSkew(BaseModel):
    company: str
    channel: str
    share: float
    signal: str
    message: str


class PaidOrganicSummary(BaseModel):
    paid_traffic: int
    organic_traffic: int
    unknown_traffic: int
    paid_share: float
    organic_share: float
    unknown_share: float


class SourceBreakdownItem(BaseModel):
    source_type: str
    traffic: int
    share: float


class TrafficBreakdownItem(BaseModel):
    traffic_type: str
    traffic: int
    share: float


class TopSourceItem(BaseModel):
    source_type: str
    traffic_type: str
    search_source: str
    traffic: int
    share: float


class OpportunitySignal(BaseModel):
    type: str
    signal: str
    message: str


class ChannelScopeAnalytics(BaseModel):
    summary: ChannelSummary
    channel_mix: list[ChannelMixItem]
    company_channel_dependency: list[CompetitorChannelDependency]
    channel_skews: list[ChannelSkew]
    paid_organic: PaidOrganicSummary
    source_type_breakdown: list[SourceBreakdownItem]
    traffic_type_breakdown: list[TrafficBreakdownItem]
    top_sources: list[TopSourceItem]
    opportunity_signals: list[OpportunitySignal]


class ChannelIntelligenceResponse(BaseModel):
    filters: ChannelIntelligenceFilters
    scope_note: str | None
    combined_scopes: bool
    overall_scope: ChannelScopeAnalytics | None
    company_scope: ChannelScopeAnalytics | None
    competitor_scope: ChannelScopeAnalytics | None


class DeviceIntelligenceFilters(BaseModel):
    project_id: UUID
    date_from: date | None
    date_to: date | None
    country: str
    tld: str
    company: str
    company_domain: str
    competitors: str
    competitor_domain: str


class DeviceSummary(BaseModel):
    visits_total: int
    desktop_visits: int
    mobile_visits: int
    desktop_share: float
    mobile_share: float
    unique_total: int
    desktop_unique: int
    mobile_unique: int
    dominant_device: str | None


class DeviceQuality(BaseModel):
    desktop_bounce_rate: float
    mobile_bounce_rate: float
    desktop_duration: float
    mobile_duration: float
    duration_total: float
    duration_gap: float
    desktop_quality_index: float
    mobile_quality_index: float
    quality_gap: float


class DeviceBounceSplit(BaseModel):
    desktop_bounce: int
    desktop_no_bounce: int
    mobile_bounce: int
    mobile_no_bounce: int
    total_bounce: int
    total_no_bounce: int
    total_bounce_rate: float


class DeviceTrendPoint(BaseModel):
    date: date
    desktop_visits: int
    mobile_visits: int
    desktop_share: float
    mobile_share: float


class CompetitorDeviceQuality(BaseModel):
    company_id: int
    company: str
    desktop_visits: int
    mobile_visits: int
    desktop_share: float
    mobile_share: float
    desktop_bounce_rate: float
    mobile_bounce_rate: float
    desktop_duration: float
    mobile_duration: float
    desktop_quality_index: float
    mobile_quality_index: float
    quality_gap: float
    signal: str


class DeviceSignal(BaseModel):
    type: str
    severity: str
    message: str


class DeviceScopeAnalytics(BaseModel):
    summary: DeviceSummary
    quality: DeviceQuality
    bounce_split: DeviceBounceSplit
    device_trend: list[DeviceTrendPoint]
    competitor_device_quality: list[CompetitorDeviceQuality]
    signals: list[DeviceSignal]


class DeviceIntelligenceResponse(BaseModel):
    filters: DeviceIntelligenceFilters
    scope_note: str | None
    combined_scopes: bool
    overall_scope: DeviceScopeAnalytics | None
    company_scope: DeviceScopeAnalytics | None
    competitor_scope: DeviceScopeAnalytics | None


class RecalculateSignalsRequest(BaseModel):
    project_id: str | None = None
    date_from: date
    date_to: date
    country: str = 'all'
    tld: str = 'all'
    company: str = 'all'
    company_domain: str = 'all'
    competitors: str = 'all'
    competitor_domain: str = 'all'
    calculation_version: str = 'v1'
    context_hash: str | None = None
    context_json: dict[str, Any] | None = None


class DerivedSignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    signal_type: str
    signal_group: str
    entity_type: str
    entity_id: str | None
    country_id: int | None
    company_id: int | None
    domain_id: int | None
    date_from: date
    date_to: date
    period_grain: str
    severity: str
    scope: str
    score: float | None
    value: float | None
    baseline_value: float | None
    delta_value: float | None
    delta_percent: float | None
    message: str
    details: dict[str, Any] | None
    calculation_version: str
    created_at: datetime


class RecalculateSignalsResponse(BaseModel):
    deleted_count: int
    inserted_count: int
    signals: list[DerivedSignalResponse]


class DerivedSignalSummary(BaseModel):
    total_signals: int
    by_group: dict[str, int]
    by_severity: dict[str, int]


class OpportunityScoreFactorBreakdown(BaseModel):
    factor: str
    raw_value: Any
    score: float
    weight: float
    weighted_score: float
    status: str
    explanation: str


class OpportunityScoreItem(BaseModel):
    country_id: int
    country: str
    country_code: str
    scope: str
    rank: int | None
    opportunity_score: float
    score_category: str
    factor_scores: dict[str, float]
    strengths: list[str]
    weaknesses: list[str]
    risks: list[str]
    explanation: dict[str, Any]
    details: dict[str, Any] | None
    calculation_version: str


class OpportunityScoresResponse(BaseModel):
    items: list[OpportunityScoreItem]
    note: str | None


class OpportunityScoreSummary(BaseModel):
    total_countries: int
    average_score: float
    top_country: str | None
    top_score: float
    by_category: dict[str, int]


class OpportunityScoreRecalculateRequest(BaseModel):
    date_from: date
    date_to: date
    country: str = 'all'
    tld: str = 'all'
    company: str = 'all'
    company_domain: str = 'all'
    competitors: str = 'all'
    competitor_domain: str = 'all'
    calculation_version: str = 'v1'
    context_hash: str | None = None
    context_json: dict[str, Any] | None = None


class OpportunityScoreRecalculateResponse(BaseModel):
    status: str
    calculation_version: str
    date_from: date
    date_to: date
    scores_created: int
    scores_updated: int
    scopes: list[str]
    note: str | None
