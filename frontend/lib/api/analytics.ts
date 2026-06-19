import { fetchApi } from '@/lib/api/client';
import type {
  AnalyticsFilterOptionsResponse,
  CompetitorIntelligenceResponse,
  CountryIntelligenceResponse,
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
