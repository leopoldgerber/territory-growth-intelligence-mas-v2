import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createMasRun, getMasRun, getMasRuns } from '@/lib/api/mas';
import type { MasRunListParams } from '@/lib/api/mas';
import type { MasWorkflowRequest } from '@/lib/types/mas';


export function useMasRunsQuery(params: MasRunListParams = {}) {
  return useQuery({
    queryKey: ['mas-runs', params],
    queryFn: () => getMasRuns(params),
    placeholderData: keepPreviousData,
  });
}

export function useMasRunQuery(runId: string | null) {
  return useQuery({
    enabled: Boolean(runId),
    queryKey: ['mas-run', runId],
    queryFn: () => getMasRun(runId as string),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'running' ? 2500 : false;
    },
  });
}

export function useCreateMasRunMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: MasWorkflowRequest) => createMasRun(request),
    onSuccess: async (response) => {
      await queryClient.invalidateQueries({ queryKey: ['mas-runs'] });
      if (response.mas_run_id) {
        await queryClient.invalidateQueries({ queryKey: ['mas-run', response.mas_run_id] });
      }
    },
  });
}
