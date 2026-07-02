import { fetchApi } from '@/lib/api/client';
import type {
  MasEvidenceBundleResponse,
  MasRunDetailResponse,
  MasRunListResponse,
  MasWorkflowRequest,
  MasWorkflowResponse,
} from '@/lib/types/mas';


export type MasRunListParams = {
  status?: string;
  intent?: string;
  strategyMode?: string;
  country?: string;
  company?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  offset?: number;
};

export function createMasRun(request: MasWorkflowRequest) {
  return fetchApi<MasWorkflowResponse>('/mas/runs', {
    body: JSON.stringify(request),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
}

export function getMasRuns(params: MasRunListParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.status) {
    searchParams.set('status', params.status);
  }
  if (params.intent) {
    searchParams.set('intent', params.intent);
  }
  if (params.strategyMode) {
    searchParams.set('strategy_mode', params.strategyMode);
  }
  if (params.country) {
    searchParams.set('country', params.country);
  }
  if (params.company) {
    searchParams.set('company', params.company);
  }
  if (params.dateFrom) {
    searchParams.set('date_from', params.dateFrom);
  }
  if (params.dateTo) {
    searchParams.set('date_to', params.dateTo);
  }
  searchParams.set('limit', String(params.limit ?? 20));
  searchParams.set('offset', String(params.offset ?? 0));
  return fetchApi<MasRunListResponse>(`/mas/runs?${searchParams.toString()}`);
}

export function getMasRun(runId: string) {
  return fetchApi<MasRunDetailResponse>(`/mas/runs/${runId}`);
}

export function getMasRunEvidence(runId: string) {
  return fetchApi<MasEvidenceBundleResponse>(`/mas/runs/${runId}/evidence`);
}
