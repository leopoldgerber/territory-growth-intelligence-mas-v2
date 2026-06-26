import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { getAnalyticsFilterOptions } from '@/lib/api/analytics';
import { generateBudgetStrategy, getBudgetStrategies, getBudgetStrategy } from '@/lib/api/reports';
import type { BudgetStrategyGenerateRequest } from '@/lib/types/reports';


export function useBudgetStrategiesQuery() {
  return useQuery({ queryKey: ['budget-strategies'], queryFn: getBudgetStrategies });
}

export function useBudgetStrategyQuery(reportId: number | null) {
  return useQuery({
    enabled: reportId !== null,
    queryKey: ['budget-strategy', reportId],
    queryFn: () => getBudgetStrategy(reportId as number),
  });
}

export function useBudgetFilterOptionsQuery(filters: BudgetStrategyGenerateRequest) {
  return useQuery({
    queryKey: [
      'budget-strategy',
      'filter-options',
      filters.date_from,
      filters.date_to,
      filters.country,
      filters.tld,
      filters.company,
      filters.company_domain,
      filters.competitors,
      filters.competitor_domain,
    ],
    queryFn: () =>
      getAnalyticsFilterOptions({
        dateFrom: filters.date_from,
        dateTo: filters.date_to,
        country: filters.country || 'all',
        tld: filters.tld,
        company: filters.company,
        companyDomain: filters.company_domain,
        competitors: filters.competitors,
        competitorDomain: filters.competitor_domain,
      }),
    placeholderData: keepPreviousData,
  });
}

export function useGenerateBudgetStrategyMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: BudgetStrategyGenerateRequest) => generateBudgetStrategy(request),
    onSuccess: async (report) => {
      queryClient.setQueryData(['budget-strategy', report.id], report);
      await queryClient.invalidateQueries({ queryKey: ['budget-strategies'] });
    },
  });
}
