'use client';

import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';

import {
  getAnalyticsFilterOptions,
  getChannelIntelligence,
  getCompetitorIntelligence,
  getCountryIntelligence,
  getDeviceIntelligence,
  getOpportunityScores,
  getOpportunityScoringSummary,
  getDerivedSignals,
  getDerivedSignalsSummary,
  recalculateDerivedSignals,
  recalculateOpportunityScores,
} from '@/lib/api/analytics';
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
    placeholderData: keepPreviousData,
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
    placeholderData: keepPreviousData,
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
    placeholderData: keepPreviousData,
  });
}

export function useChannelIntelligenceQuery() {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));

  return useQuery({
    queryKey: [
      'channel-intelligence',
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
      getChannelIntelligence({
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
    placeholderData: keepPreviousData,
  });
}

export function useDeviceIntelligenceQuery() {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));

  return useQuery({
    queryKey: [
      'device-intelligence',
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
      getDeviceIntelligence({
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
    placeholderData: keepPreviousData,
  });
}

export function useDerivedSignalsQuery(scope: 'overall' | 'company' | 'competitor', enabled = true) {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));
  const signalGroup = searchParams.get('signalGroup') ?? 'all';
  const severity = searchParams.get('severity') ?? 'all';

  return useQuery({
    enabled,
    queryKey: [
      'derived-signals',
      filters.dateFrom,
      filters.dateTo,
      filters.country,
      filters.tld,
      filters.company,
      filters.companyDomain,
      filters.competitors,
      filters.competitorDomain,
      signalGroup,
      severity,
      scope,
    ],
    queryFn: () =>
      getDerivedSignals({
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        signalGroup,
        severity,
        scope,
        limit: 100,
      }),
    placeholderData: keepPreviousData,
  });
}

export function useDerivedSignalsSummaryQuery(scope: 'overall' | 'company' | 'competitor', enabled = true) {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));
  const signalGroup = searchParams.get('signalGroup') ?? 'all';
  const severity = searchParams.get('severity') ?? 'all';

  return useQuery({
    enabled,
    queryKey: [
      'derived-signals-summary',
      filters.dateFrom,
      filters.dateTo,
      filters.country,
      filters.tld,
      filters.company,
      filters.companyDomain,
      filters.competitors,
      filters.competitorDomain,
      signalGroup,
      severity,
      scope,
    ],
    queryFn: () =>
      getDerivedSignalsSummary({
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        signalGroup,
        severity,
        scope,
      }),
    placeholderData: keepPreviousData,
  });
}

export function useRecalculateDerivedSignalsMutation() {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      recalculateDerivedSignals({
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        country: filters.country,
        tld: filters.tld,
        company: filters.company,
        company_domain: filters.companyDomain,
        competitors: filters.competitors,
        competitor_domain: filters.competitorDomain,
        calculation_version: 'v1',
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['derived-signals'] }),
        queryClient.invalidateQueries({ queryKey: ['derived-signals-summary'] }),
      ]);
    },
  });
}

export function useOpportunityScoresQuery(scope: 'overall' | 'company' | 'competitor', enabled = true) {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));

  return useQuery({
    enabled,
    queryKey: [
      'opportunity-scores',
      filters.dateFrom,
      filters.dateTo,
      filters.country,
      filters.tld,
      filters.company,
      filters.companyDomain,
      filters.competitors,
      filters.competitorDomain,
      scope,
    ],
    queryFn: () =>
      getOpportunityScores({
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        country: filters.country,
        scope,
        limit: 100,
      }),
    placeholderData: keepPreviousData,
  });
}

export function useOpportunityScoringSummaryQuery(scope: 'overall' | 'company' | 'competitor', enabled = true) {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));

  return useQuery({
    enabled,
    queryKey: [
      'opportunity-scoring-summary',
      filters.dateFrom,
      filters.dateTo,
      filters.country,
      filters.tld,
      filters.company,
      filters.companyDomain,
      filters.competitors,
      filters.competitorDomain,
      scope,
    ],
    queryFn: () =>
      getOpportunityScoringSummary({
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        country: filters.country,
        scope,
      }),
    placeholderData: keepPreviousData,
  });
}

export function useRecalculateOpportunityScoresMutation() {
  const searchParams = useSearchParams();
  const filters = readDashboardFilters(new URLSearchParams(searchParams.toString()));
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      recalculateOpportunityScores({
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        country: filters.country,
        tld: filters.tld,
        company: filters.company,
        company_domain: filters.companyDomain,
        competitors: filters.competitors,
        competitor_domain: filters.competitorDomain,
        calculation_version: 'v1',
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['opportunity-scores'] }),
        queryClient.invalidateQueries({ queryKey: ['opportunity-scoring-summary'] }),
      ]);
    },
  });
}
