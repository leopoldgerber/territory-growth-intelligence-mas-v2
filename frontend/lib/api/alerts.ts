import { fetchApi } from '@/lib/api/client';
import type {
  AlertDetectResponse,
  AlertListParams,
  AlertListResponse,
  AlertSummary,
  UpdateStatusResponse,
} from '@/lib/types/alerts';


export function getAlerts(params: AlertListParams = {}) {
  const searchParams = buildParams(params);
  return fetchApi<AlertListResponse>(`/alerts?${searchParams.toString()}`);
}

export function getAlertSummary(params: AlertListParams = {}) {
  const searchParams = buildParams(params);
  return fetchApi<AlertSummary>(`/alerts/summary?${searchParams.toString()}`);
}

export function getUpdateStatus() {
  return fetchApi<UpdateStatusResponse>('/alerts/status');
}

export function detectAlerts() {
  return fetchApi<AlertDetectResponse>('/alerts/detect', {
    body: JSON.stringify({ run_recalculation: true }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
}

export function updateAlertStatus(alertId: string, status: string) {
  return fetchApi(`/alerts/${alertId}/status`, {
    body: JSON.stringify({ status }),
    headers: { 'Content-Type': 'application/json' },
    method: 'PATCH',
  });
}

function buildParams(params: AlertListParams) {
  const searchParams = new URLSearchParams();
  if (params.alertType) {
    searchParams.set('alert_type', params.alertType);
  }
  if (params.severity) {
    searchParams.set('severity', params.severity);
  }
  if (params.status) {
    searchParams.set('status', params.status);
  }
  searchParams.set('limit', String(params.limit ?? 30));
  searchParams.set('offset', String(params.offset ?? 0));
  return searchParams;
}
