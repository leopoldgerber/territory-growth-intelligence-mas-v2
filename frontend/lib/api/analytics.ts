import { fetchApi } from '@/lib/api/client';
import type {
  AnalyticsFilterOptionsResponse,
  ChannelIntelligenceResponse,
  CompetitorIntelligenceResponse,
  CountryIntelligenceResponse,
  DeviceIntelligenceResponse,
  DerivedSignal,
  DerivedSignalSummary,
  RecalculateSignalsRequest,
  RecalculateSignalsResponse,
  OpportunityScoreRecalculateRequest,
  OpportunityScoreRecalculateResponse,
  OpportunityScoresResponse,
  OpportunityScoreSummary,
  OpportunityScoreScope,
} from '@/lib/types/analytics';

export type CountryIntelligenceParams = {
  dateFrom: string;
  dateTo: string;
  country: string;
  tld: string;
  company: string;
  companyDomain: string;
  competitors: string;
  competitorDomain: string;
  limit?: number;
};

export function getCountryIntelligence(params: CountryIntelligenceParams) {
  const searchParams = new URLSearchParams();
  searchParams.set('dateFrom', params.dateFrom);
  searchParams.set('dateTo', params.dateTo);
  searchParams.set('country', params.country);
  searchParams.set('tld', params.tld);
  searchParams.set('company', params.company);
  searchParams.set('companyDomain', params.companyDomain);
  searchParams.set('competitors', params.competitors);
  searchParams.set('competitorDomain', params.competitorDomain);
  searchParams.set('limit', String(params.limit ?? 10));

  return fetchApi<CountryIntelligenceResponse>(`/analytics/country-intelligence?${searchParams.toString()}`);
}

export function getCompetitorIntelligence(params: CountryIntelligenceParams) {
  const searchParams = new URLSearchParams();
  searchParams.set('dateFrom', params.dateFrom);
  searchParams.set('dateTo', params.dateTo);
  searchParams.set('country', params.country);
  searchParams.set('tld', params.tld);
  searchParams.set('competitors', params.competitors);
  searchParams.set('competitorDomain', params.competitorDomain);
  searchParams.set('limit', String(params.limit ?? 10));

  return fetchApi<CompetitorIntelligenceResponse>(`/analytics/competitor-intelligence?${searchParams.toString()}`);
}

export function getChannelIntelligence(params: CountryIntelligenceParams) {
  const searchParams = new URLSearchParams();
  searchParams.set('dateFrom', params.dateFrom);
  searchParams.set('dateTo', params.dateTo);
  searchParams.set('country', params.country);
  searchParams.set('tld', params.tld);
  searchParams.set('company', params.company);
  searchParams.set('companyDomain', params.companyDomain);
  searchParams.set('competitors', params.competitors);
  searchParams.set('competitorDomain', params.competitorDomain);
  searchParams.set('limit', String(params.limit ?? 10));

  return fetchApi<ChannelIntelligenceResponse>(`/analytics/channel-intelligence?${searchParams.toString()}`);
}

export function getDeviceIntelligence(params: CountryIntelligenceParams) {
  const searchParams = new URLSearchParams();
  searchParams.set('dateFrom', params.dateFrom);
  searchParams.set('dateTo', params.dateTo);
  searchParams.set('country', params.country);
  searchParams.set('tld', params.tld);
  searchParams.set('company', params.company);
  searchParams.set('companyDomain', params.companyDomain);
  searchParams.set('competitors', params.competitors);
  searchParams.set('competitorDomain', params.competitorDomain);
  searchParams.set('limit', String(params.limit ?? 10));

  return fetchApi<DeviceIntelligenceResponse>(`/analytics/device-intelligence?${searchParams.toString()}`);
}

export type DerivedSignalParams = {
  dateFrom: string;
  dateTo: string;
  signalGroup: string;
  severity: string;
  scope: 'overall' | 'company' | 'competitor';
  limit?: number;
};

function buildSignalParams(params: DerivedSignalParams): URLSearchParams {
  const searchParams = new URLSearchParams();
  searchParams.set('dateFrom', params.dateFrom);
  searchParams.set('dateTo', params.dateTo);
  searchParams.set('signalGroup', params.signalGroup);
  searchParams.set('severity', params.severity);
  searchParams.set('scope', params.scope);
  searchParams.set('limit', String(params.limit ?? 100));
  return searchParams;
}

export function getDerivedSignals(params: DerivedSignalParams) {
  const searchParams = buildSignalParams(params);
  return fetchApi<DerivedSignal[]>(`/analytics/signals?${searchParams.toString()}`);
}

export function getDerivedSignalsSummary(params: DerivedSignalParams) {
  const searchParams = buildSignalParams(params);
  searchParams.delete('limit');
  return fetchApi<DerivedSignalSummary>(`/analytics/signals/summary?${searchParams.toString()}`);
}

export function recalculateDerivedSignals(request: RecalculateSignalsRequest) {
  return fetchApi<RecalculateSignalsResponse>('/analytics/signals/recalculate', {
    body: JSON.stringify(request),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });
}

export type OpportunityScoreParams = {
  dateFrom: string;
  dateTo: string;
  country: string;
  scope: OpportunityScoreScope;
  scoreCategory?: string;
  limit?: number;
};

function buildScoringParams(params: OpportunityScoreParams): URLSearchParams {
  const searchParams = new URLSearchParams();
  searchParams.set('dateFrom', params.dateFrom);
  searchParams.set('dateTo', params.dateTo);
  searchParams.set('country', params.country);
  searchParams.set('scope', params.scope);
  searchParams.set('scoreCategory', params.scoreCategory ?? 'all');
  searchParams.set('limit', String(params.limit ?? 100));
  return searchParams;
}

export function getOpportunityScores(params: OpportunityScoreParams) {
  const searchParams = buildScoringParams(params);
  return fetchApi<OpportunityScoresResponse>(`/analytics/scoring/opportunities?${searchParams.toString()}`);
}

export function getOpportunityScoringSummary(params: OpportunityScoreParams) {
  const searchParams = buildScoringParams(params);
  searchParams.delete('limit');
  return fetchApi<OpportunityScoreSummary>(`/analytics/scoring/summary?${searchParams.toString()}`);
}

export function recalculateOpportunityScores(request: OpportunityScoreRecalculateRequest) {
  return fetchApi<OpportunityScoreRecalculateResponse>('/analytics/scoring/recalculate', {
    body: JSON.stringify(request),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });
}

export function getAnalyticsFilterOptions(params: CountryIntelligenceParams) {
  const searchParams = new URLSearchParams();
  searchParams.set('dateFrom', params.dateFrom);
  searchParams.set('dateTo', params.dateTo);
  searchParams.set('country', params.country);
  searchParams.set('tld', params.tld);
  searchParams.set('company', params.company);
  searchParams.set('companyDomain', params.companyDomain);
  searchParams.set('competitors', params.competitors);
  searchParams.set('competitorDomain', params.competitorDomain);

  return fetchApi<AnalyticsFilterOptionsResponse>(`/analytics/filter-options?${searchParams.toString()}`);
}
