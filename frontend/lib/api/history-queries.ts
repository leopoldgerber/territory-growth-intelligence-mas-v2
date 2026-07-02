import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  getHistoryInsights,
  getHistoryMasRuns,
  getHistoryRecommendations,
  getHistoryReports,
  updateHistoryRecommendationStatus,
} from '@/lib/api/history';
import type { HistoryListParams } from '@/lib/types/history';


export function useHistoryMasRunsQuery(params: HistoryListParams = {}) {
  return useQuery({
    queryKey: ['history', 'mas-runs', params],
    queryFn: () => getHistoryMasRuns(params),
    placeholderData: keepPreviousData,
  });
}

export function useHistoryReportsQuery(params: HistoryListParams = {}) {
  return useQuery({
    queryKey: ['history', 'reports', params],
    queryFn: () => getHistoryReports(params),
    placeholderData: keepPreviousData,
  });
}

export function useHistoryInsightsQuery(params: HistoryListParams = {}) {
  return useQuery({
    queryKey: ['history', 'insights', params],
    queryFn: () => getHistoryInsights(params),
    placeholderData: keepPreviousData,
  });
}

export function useHistoryRecommendationsQuery(params: HistoryListParams = {}) {
  return useQuery({
    queryKey: ['history', 'recommendations', params],
    queryFn: () => getHistoryRecommendations(params),
    placeholderData: keepPreviousData,
  });
}

export function useUpdateRecommendationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: { recommendationId: string; status: string; userDecision?: string }) => (
      updateHistoryRecommendationStatus(request.recommendationId, request.status, request.userDecision)
    ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['history', 'recommendations'] });
    },
  });
}
