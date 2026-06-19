export type CountryIntelligenceFilters = {
  project_id: string;
  date_from: string | null;
  date_to: string | null;
  country: string;
  tld: string;
  company: string;
  company_domain: string;
  competitors: string;
  competitor_domain: string;
};

export type FilterOption = {
  label: string;
  value: string;
};

export type DomainFilterOption = FilterOption & {
  company_id: number;
  tld: string | null;
};

export type AnalyticsFilterOptionsResponse = {
  countries: FilterOption[];
  tlds: FilterOption[];
  companies: FilterOption[];
  domains: DomainFilterOption[];
};

export type CountryIntelligenceSummary = {
  total_traffic: number;
  active_competitors: number;
  active_domains: number;
  country_count: number;
  date_count: number;
};

export type TopCompetitor = {
  company_id: number;
  company: string;
  traffic: number;
  traffic_share: number;
  domains_count: number;
};

export type TrafficTrendPoint = {
  date: string;
  traffic: number;
};

export type DeviceSplit = {
  desktop_traffic: number;
  mobile_traffic: number;
  desktop_share: number;
  mobile_share: number;
};

export type BounceSummary = {
  no_bounce: number;
  bounce: number;
  bounce_rate: number;
};

export type EngagementMetrics = {
  unique_visitors: number;
  pages_per_visit: number;
  avg_visit_duration: number;
};

export type MarketSignal = {
  status: string;
  growth_rate: number;
  message: string;
};

export type CountryIntelligenceResponse = {
  filters: CountryIntelligenceFilters;
  selected_country_count: number;
  summary: CountryIntelligenceSummary;
  competitor_summary: CountryIntelligenceSummary;
  top_competitors: TopCompetitor[];
  traffic_trend: TrafficTrendPoint[];
  competitor_traffic_trend: TrafficTrendPoint[];
  device_split: DeviceSplit;
  competitor_device_split: DeviceSplit;
  bounce: BounceSummary;
  competitor_bounce: BounceSummary;
  engagement: EngagementMetrics;
  competitor_engagement: EngagementMetrics;
  market_signal: MarketSignal;
  competitor_market_signal: MarketSignal;
};

export type CompetitorIntelligenceFilters = {
  project_id: string;
  date_from: string | null;
  date_to: string | null;
  competitors: string;
  competitor_domain: string;
  country: string;
  tld: string;
};

export type CompetitorSummary = {
  total_traffic: number;
  active_countries: number;
  active_domains: number;
  top_country: string | null;
  top_country_share: number;
  growth_rate: number;
};

export type CompetitorCountryMetric = {
  country_id: number;
  country: string;
  country_code: string;
  traffic: number;
  traffic_share: number;
  growth_rate: number;
  growth_status: string;
  status: string;
};

export type CompetitorDependency = {
  top1_country_share: number;
  top3_country_share: number;
  dependency_level: string;
};

export type PresenceStability = {
  active_days: number;
  period_days: number;
  stability_rate: number;
  status: string;
};

export type MarketWindow = {
  country: string;
  signal: string;
  message: string;
};

export type CompetitorIntelligenceResponse = {
  filters: CompetitorIntelligenceFilters;
  summary: CompetitorSummary;
  top_countries: CompetitorCountryMetric[];
  growing_countries: CompetitorCountryMetric[];
  declining_countries: CompetitorCountryMetric[];
  anchor_markets: CompetitorCountryMetric[];
  peripheral_markets: CompetitorCountryMetric[];
  dependency: CompetitorDependency;
  presence_stability: PresenceStability;
  market_windows: MarketWindow[];
};
