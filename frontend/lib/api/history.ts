import { fetchApi } from '@/lib/api/client';
import type {
  HistoryListParams,
  HistoryMasRunListResponse,
  InsightListResponse,
  Recommendation,
  RecommendationListResponse,
  ReportSnapshotListResponse,
} from '@/lib/types/history';


export function getHistoryMasRuns(params: HistoryListParams = {}) {
  return fetchApi<HistoryMasRunListResponse>(`/history/mas-runs?${buildParams(params).toString()}`);
}

export function getHistoryReports(params: HistoryListParams = {}) {
  return fetchApi<ReportSnapshotListResponse>(`/history/reports?${buildParams(params).toString()}`);
}

export function getHistoryInsights(params: HistoryListParams = {}) {
  return fetchApi<InsightListResponse>(`/history/insights?${buildParams(params).toString()}`);
}

export function getHistoryRecommendations(params: HistoryListParams = {}) {
  return fetchApi<RecommendationListResponse>(`/history/recommendations?${buildParams(params).toString()}`);
}

export function updateHistoryRecommendationStatus(
  recommendationId: string,
  status: string,
  userDecision?: string,
) {
  return fetchApi<Recommendation>(`/history/recommendations/${recommendationId}/status`, {
    body: JSON.stringify({
      status,
      user_decision: userDecision ?? null,
      user_decision_reason: null,
    }),
    headers: { 'Content-Type': 'application/json' },
    method: 'PATCH',
  });
}

function buildParams(params: HistoryListParams): URLSearchParams {
  const searchParams = new URLSearchParams();
  if (params.search) {
    searchParams.set('search', params.search);
  }
  if (params.status) {
    searchParams.set('status', params.status);
  }
  if (params.strategyMode) {
    searchParams.set('strategy_mode', params.strategyMode);
  }
  searchParams.set('limit', String(params.limit ?? 20));
  searchParams.set('offset', String(params.offset ?? 0));
  return searchParams;
}
