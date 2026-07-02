import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { detectAlerts, getAlertSummary, getAlerts, getUpdateStatus, updateAlertStatus } from '@/lib/api/alerts';
import type { AlertListParams } from '@/lib/types/alerts';


export function useAlertsQuery(params: AlertListParams = {}) {
  return useQuery({
    queryKey: ['alerts', params],
    queryFn: () => getAlerts(params),
    placeholderData: keepPreviousData,
  });
}

export function useAlertSummaryQuery(params: AlertListParams = {}) {
  return useQuery({
    queryKey: ['alerts-summary', params],
    queryFn: () => getAlertSummary(params),
    placeholderData: keepPreviousData,
  });
}

export function useUpdateStatusQuery() {
  return useQuery({
    queryKey: ['alerts-update-status'],
    queryFn: () => getUpdateStatus(),
  });
}

export function useDetectAlertsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => detectAlerts(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
      await queryClient.invalidateQueries({ queryKey: ['alerts-summary'] });
      await queryClient.invalidateQueries({ queryKey: ['alerts-update-status'] });
    },
  });
}

export function useAlertStatusMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: { alertId: string; status: string }) => updateAlertStatus(request.alertId, request.status),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
      await queryClient.invalidateQueries({ queryKey: ['alerts-summary'] });
    },
  });
}
