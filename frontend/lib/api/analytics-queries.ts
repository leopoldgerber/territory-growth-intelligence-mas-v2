'use client';

import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';

import { getAnalyticsFilterOptions, getCompetitorIntelligence, getCountryIntelligence } from '@/lib/api/analytics';
import { readDashboardFilters } from '@/lib/dashboard/query-params';

export function useAnalyticsFilterOptionsQuery() {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));

  return useQuery({
    queryKey: [
      'analytics',
      'filter-options',
      filters.dateFrom,
      filters.dateTo,
      filters.country,
      filters.tld,
      filters.company,
      filters.companyDomain,
      filters.competitors,
      filters.competitorDomain,
    ],
    queryFn: () =>
      getAnalyticsFilterOptions({
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        country: filters.country,
        tld: filters.tld,
        company: filters.company,
        companyDomain: filters.companyDomain,
        competitors: filters.competitors,
        competitorDomain: filters.competitorDomain,
      }),
  });
}

export function useCountryIntelligenceQuery() {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));

  return useQuery({
    queryKey: [
      'country-intelligence',
      filters.dateFrom,
      filters.dateTo,
      filters.country,
      filters.tld,
      filters.company,
      filters.companyDomain,
      filters.competitors,
      filters.competitorDomain,
    ],
    queryFn: () =>
      getCountryIntelligence({
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        country: filters.country,
        tld: filters.tld,
        company: filters.company,
        companyDomain: filters.companyDomain,
        competitors: filters.competitors,
        competitorDomain: filters.competitorDomain,
        limit: 10,
      }),
  });
}

export function useCompetitorIntelligenceQuery() {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));

  return useQuery({
    queryKey: [
      'competitor-intelligence',
      filters.dateFrom,
      filters.dateTo,
      filters.country,
      filters.tld,
      filters.competitors,
      filters.competitorDomain,
    ],
    queryFn: () =>
      getCompetitorIntelligence({
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        country: filters.country,
        tld: filters.tld,
        company: filters.company,
        companyDomain: filters.companyDomain,
        competitors: filters.competitors,
        competitorDomain: filters.competitorDomain,
        limit: 10,
      }),
  });
}
