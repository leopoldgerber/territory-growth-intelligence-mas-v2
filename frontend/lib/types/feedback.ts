export type RecommendationDecision = {
  id: string;
  project_id: string;
  recommendation_id: string;
  mas_run_id: string | null;
  user_id: string | null;
  decision: string;
  reason_category: string;
  reason_text: string | null;
  expected_action_json: Record<string, unknown>;
  created_at: string;
};

export type ActionExecution = {
  id: string;
  project_id: string;
  recommendation_id: string | null;
  country_id: number | null;
  company_id: number | null;
  strategy_mode: string | null;
  action_type: string;
  channel: string | null;
  planned_budget: string | null;
  actual_budget: string | null;
  currency: string | null;
  start_date: string | null;
  end_date: string | null;
  status: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ActionResult = {
  id: string;
  project_id: string;
  action_execution_id: string;
  recommendation_id: string | null;
  period_from: string | null;
  period_to: string | null;
  channel: string | null;
  country_id: number | null;
  company_id: number | null;
  traffic: number | null;
  traffic_growth: string | null;
  bounce_rate: string | null;
  avg_visit_duration: string | null;
  pages_per_visit: string | null;
  spend: string | null;
  conversions: string | null;
  revenue: string | null;
  cac: string | null;
  cpa: string | null;
  roi: string | null;
  payback_days: number | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type LearningEvent = {
  id: string;
  project_id: string;
  source_type: string;
  source_record_id: string | null;
  recommendation_id: string | null;
  action_execution_id: string | null;
  learning_type: string;
  country_id: number | null;
  company_id: number | null;
  channel: string | null;
  summary: string;
  details_json: Record<string, unknown>;
  impact_area: string;
  confidence: string;
  status: string;
  created_at: string;
};

export type ModelReview = {
  id: string;
  project_id: string;
  source_learning_event_id: string | null;
  model_name: string;
  current_version: string;
  proposed_version: string | null;
  proposed_changes_json: Record<string, unknown>;
  reason: string;
  status: string;
  created_at: string;
  reviewed_at: string | null;
  applied_at: string | null;
};

export type ActionExecutionListResponse = {
  items: ActionExecution[];
  total: number;
};

export type LearningEventListResponse = {
  items: LearningEvent[];
  total: number;
};

export type ModelReviewListResponse = {
  items: ModelReview[];
  total: number;
};

export type OutcomeComparison = {
  recommendation_id: string;
  classification: string;
  outcome_score: number;
  learning_event: LearningEvent;
  notes: string[];
  assumptions_updated: number;
  model_review: ModelReview | null;
};
