import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

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
