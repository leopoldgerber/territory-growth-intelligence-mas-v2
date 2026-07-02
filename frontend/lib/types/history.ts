import type { MasRunListResponse } from '@/lib/types/mas';

export type ReportSnapshot = {
  id: string;
  project_id: string;
  report_type: string;
  source_type: string;
  source_record_id: string | null;
  mas_run_id: string | null;
  context_hash: string | null;
  strategy_mode: string | null;
  country_id: number | null;
  company_id: number | null;
  company_domain: string | null;
  period_from: string | null;
  period_to: string | null;
  budget_amount: string | null;
  currency: string | null;
  calculation_version: string | null;
  scoring_version: string | null;
  prompt_version_id: number | null;
  llm_provider: string | null;
  llm_model: string | null;
  title: string;
  summary: string;
  report_json: Record<string, unknown>;
  markdown_snapshot: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Insight = {
  id: string;
  project_id: string;
  source_type: string;
  source_record_id: string | null;
  mas_run_id: string | null;
  report_snapshot_id: string | null;
  evidence_item_id: string | null;
  insight_type: string;
  category: string | null;
  severity: string | null;
  country_id: number | null;
  company_id: number | null;
  strategy_mode: string | null;
  period_from: string | null;
  period_to: string | null;
  title: string;
  summary: string;
  details_json: Record<string, unknown>;
  confidence: string;
  status: string;
  tags: string[];
  created_at: string;
  updated_at: string;
};

export type Recommendation = {
  id: string;
  project_id: string;
  source_type: string;
  source_record_id: string | null;
  mas_run_id: string | null;
  report_snapshot_id: string | null;
  insight_id: string | null;
  recommendation_type: string;
  strategy_mode: string | null;
  country_id: number | null;
  company_id: number | null;
  period_from: string | null;
  period_to: string | null;
  title: string;
  description: string;
  action: string;
  priority: string;
  channel: string | null;
  budget_share: string | null;
  budget_amount: string | null;
  currency: string | null;
  confidence: string;
  status: string;
  user_decision: string | null;
  user_decision_reason: string | null;
  linked_mas_run_id: string | null;
  linked_evidence_item_ids: string[];
  created_at: string;
  updated_at: string;
};

export type HistoryListParams = {
  search?: string;
  status?: string;
  strategyMode?: string;
  limit?: number;
  offset?: number;
};

export type ReportSnapshotListResponse = {
  items: ReportSnapshot[];
  total: number;
};

export type InsightListResponse = {
  items: Insight[];
  total: number;
};

export type RecommendationListResponse = {
  items: Recommendation[];
  total: number;
};

export type HistoryMasRunListResponse = MasRunListResponse;
