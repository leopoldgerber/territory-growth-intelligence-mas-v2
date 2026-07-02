export type AlertEvent = {
  id: string;
  project_id: string;
  alert_rule_id: number | null;
  alert_type: string;
  severity: string;
  status: string;
  country_id: number | null;
  company_id: number | null;
  competitor_id: number | null;
  channel: string | null;
  period_from: string | null;
  period_to: string | null;
  title: string;
  summary: string;
  details_json: Record<string, unknown>;
  evidence_refs_json: Array<Record<string, unknown>>;
  related_signal_ids: number[];
  related_score_ids: number[];
  related_insight_ids: string[];
  context_hash: string | null;
  dedupe_key: string;
  detected_at: string;
  created_at: string;
  updated_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
};

export type AlertSummary = {
  total: number;
  new_alerts: number;
  high_severity: number;
  market_windows: number;
  competitor_movements: number;
  quality_risks: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
};

export type DataFreshnessStatus = {
  id: number;
  project_id: string;
  dataset_type: string;
  latest_available_date: string | null;
  latest_loaded_date: string | null;
  last_update_batch_id: string | null;
  freshness_status: string;
  lag_days: number | null;
  updated_at: string;
};

export type DataUpdateBatch = {
  id: string;
  project_id: string;
  source_type: string;
  source_file: string | null;
  period_from: string | null;
  period_to: string | null;
  status: string;
  rows_loaded: number;
  rows_failed: number;
  validation_status: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  error_message: string | null;
  metadata_json: Record<string, unknown>;
};

export type RecalculationJob = {
  id: string;
  project_id: string;
  data_update_batch_id: string | null;
  job_type: string;
  status: string;
  period_from: string | null;
  period_to: string | null;
  calculation_version: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  metrics_json: Record<string, unknown>;
};

export type AlertListResponse = {
  items: AlertEvent[];
  total: number;
};

export type AlertDetectResponse = {
  status: string;
  data_update_batch_id: string | null;
  jobs: RecalculationJob[];
  alerts_created: number;
  alerts_updated: number;
  alerts: AlertEvent[];
};

export type UpdateStatusResponse = {
  freshness: DataFreshnessStatus[];
  latest_batches: DataUpdateBatch[];
  latest_jobs: RecalculationJob[];
};

export type AlertListParams = {
  alertType?: string;
  severity?: string;
  status?: string;
  limit?: number;
  offset?: number;
};
