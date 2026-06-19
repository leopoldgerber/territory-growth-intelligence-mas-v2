from datetime import date
from uuid import UUID

from pydantic import BaseModel


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
