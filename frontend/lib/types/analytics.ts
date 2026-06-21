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

export type ChannelIntelligenceFilters = {
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

export type ChannelSummary = {
  total_traffic: number;
  dominant_channel: string | null;
  dominant_channel_share: number;
  paid_share: number;
  organic_share: number;
  competitors_count: number;
  domains_count: number;
};

export type ChannelMixItem = {
  channel: string;
  traffic: number;
  share: number;
};

export type CompetitorChannelDependency = {
  company_id: number;
  company: string;
  total_traffic: number;
  dominant_channel: string | null;
  dominant_channel_share: number;
  direct_share: number;
  search_share: number;
  paid_share: number;
  referral_share: number;
  social_share: number;
  dependency_level: string;
};

export type ChannelSkew = {
  company: string;
  channel: string;
  share: number;
  signal: string;
  message: string;
};

export type PaidOrganicSummary = {
  paid_traffic: number;
  organic_traffic: number;
  unknown_traffic: number;
  paid_share: number;
  organic_share: number;
  unknown_share: number;
};

export type SourceBreakdownItem = {
  source_type: string;
  traffic: number;
  share: number;
};

export type TrafficBreakdownItem = {
  traffic_type: string;
  traffic: number;
  share: number;
};

export type TopSourceItem = {
  source_type: string;
  traffic_type: string;
  search_source: string;
  traffic: number;
  share: number;
};

export type OpportunitySignal = {
  type: string;
  signal: string;
  message: string;
};

export type ChannelScopeAnalytics = {
  summary: ChannelSummary;
  channel_mix: ChannelMixItem[];
  company_channel_dependency: CompetitorChannelDependency[];
  channel_skews: ChannelSkew[];
  paid_organic: PaidOrganicSummary;
  source_type_breakdown: SourceBreakdownItem[];
  traffic_type_breakdown: TrafficBreakdownItem[];
  top_sources: TopSourceItem[];
  opportunity_signals: OpportunitySignal[];
};

export type ChannelIntelligenceResponse = {
  filters: ChannelIntelligenceFilters;
  scope_note: string | null;
  combined_scopes: boolean;
  overall_scope: ChannelScopeAnalytics | null;
  company_scope: ChannelScopeAnalytics | null;
  competitor_scope: ChannelScopeAnalytics | null;
};

export type DeviceIntelligenceFilters = {
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

export type DeviceSummary = {
  visits_total: number;
  desktop_visits: number;
  mobile_visits: number;
  desktop_share: number;
  mobile_share: number;
  unique_total: number;
  desktop_unique: number;
  mobile_unique: number;
  dominant_device: string | null;
};

export type DeviceQuality = {
  desktop_bounce_rate: number;
  mobile_bounce_rate: number;
  desktop_duration: number;
  mobile_duration: number;
  duration_total: number;
  duration_gap: number;
  desktop_quality_index: number;
  mobile_quality_index: number;
  quality_gap: number;
};

export type DeviceBounceSplit = {
  desktop_bounce: number;
  desktop_no_bounce: number;
  mobile_bounce: number;
  mobile_no_bounce: number;
  total_bounce: number;
  total_no_bounce: number;
  total_bounce_rate: number;
};

export type DeviceTrendPoint = {
  date: string;
  desktop_visits: number;
  mobile_visits: number;
  desktop_share: number;
  mobile_share: number;
};

export type CompetitorDeviceQuality = {
  company_id: number;
  company: string;
  desktop_visits: number;
  mobile_visits: number;
  desktop_share: number;
  mobile_share: number;
  desktop_bounce_rate: number;
  mobile_bounce_rate: number;
  desktop_duration: number;
  mobile_duration: number;
  desktop_quality_index: number;
  mobile_quality_index: number;
  quality_gap: number;
  signal: string;
};

export type DeviceSignal = {
  type: string;
  severity: string;
  message: string;
};

export type DeviceScopeAnalytics = {
  summary: DeviceSummary;
  quality: DeviceQuality;
  bounce_split: DeviceBounceSplit;
  device_trend: DeviceTrendPoint[];
  competitor_device_quality: CompetitorDeviceQuality[];
  signals: DeviceSignal[];
};

export type DeviceIntelligenceResponse = {
  filters: DeviceIntelligenceFilters;
  scope_note: string | null;
  combined_scopes: boolean;
  overall_scope: DeviceScopeAnalytics | null;
  company_scope: DeviceScopeAnalytics | null;
  competitor_scope: DeviceScopeAnalytics | null;
};

export type DerivedSignalGroup = 'growth' | 'volatility' | 'competition' | 'territory' | 'channel' | 'quality' | 'device';

export type DerivedSignalSeverity = 'low' | 'medium' | 'high' | 'critical';

export type DerivedSignal = {
  id: number;
  signal_type: string;
  signal_group: DerivedSignalGroup;
  entity_type: string;
  entity_id: string | null;
  country_id: number | null;
  company_id: number | null;
  domain_id: number | null;
  date_from: string;
  date_to: string;
  period_grain: string;
  severity: DerivedSignalSeverity;
  scope: 'overall' | 'company' | 'competitor';
  score: number | null;
  value: number | null;
  baseline_value: number | null;
  delta_value: number | null;
  delta_percent: number | null;
  message: string;
  details: Record<string, unknown> | null;
  calculation_version: string;
  created_at: string;
};

export type DerivedSignalSummary = {
  total_signals: number;
  by_group: Partial<Record<DerivedSignalGroup, number>>;
  by_severity: Partial<Record<DerivedSignalSeverity, number>>;
};

export type RecalculateSignalsRequest = {
  project_id?: string | null;
  date_from: string;
  date_to: string;
  country: string;
  tld: string;
  company: string;
  company_domain: string;
  competitors: string;
  competitor_domain: string;
  calculation_version: string;
};

export type RecalculateSignalsResponse = {
  deleted_count: number;
  inserted_count: number;
  signals: DerivedSignal[];
};
