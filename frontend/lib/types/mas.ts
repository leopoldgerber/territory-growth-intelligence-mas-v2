export type MasRunStatus =
  | 'pending'
  | 'running'
  | 'needs_clarification'
  | 'completed'
  | 'partial'
  | 'failed'
  | 'skipped'
  | 'cancelled';

export type MasStrategyMode = 'market_entry' | 'existing_presence';

export type MasRunOptions = {
  use_rag: boolean;
  save_result: boolean;
  run_mode: 'sync' | 'async';
};

export type MasDefaultContext = {
  project_id?: string | null;
  strategy_mode: MasStrategyMode;
  country: string | null;
  company: string | null;
  date_from: string;
  date_to: string;
  budget_amount: number;
  currency: 'USD' | 'EUR';
};

export type MasWorkflowRequest = {
  project_id?: string | null;
  user_query: string;
  default_context: MasDefaultContext;
  options: MasRunOptions;
};

export type MasWorkflowResponse = {
  mas_run_id: string;
  status: MasRunStatus;
  resolved_intent: string | null;
  resolved_context: Record<string, unknown>;
  final_answer: string | null;
  final_summary: string | null;
  confidence: string | null;
  evidence_count: number;
  warnings: string[];
  clarification_questions: string[];
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type MasRunSummary = {
  id: string;
  project_id: string;
  status: MasRunStatus;
  user_query: string;
  resolved_intent: string | null;
  resolved_context_json: Record<string, unknown>;
  strategy_mode: MasStrategyMode | null;
  country: string | null;
  company: string | null;
  final_summary: string | null;
  date_from: string | null;
  date_to: string | null;
  rag_status: string | null;
  rag_results_count: number;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type MasRunListResponse = {
  items: MasRunSummary[];
  total: number;
};

export type MasToolCall = {
  id: string;
  mas_run_id: string;
  agent_run_id: string | null;
  tool_name: string;
  tool_type: string;
  status: MasRunStatus;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown> | null;
  error_message: string | null;
  duration_ms: number | null;
  created_at: string;
};

export type MasEvidenceItem = {
  id: string;
  mas_run_id: string;
  source_type: string;
  evidence_type: string;
  source_table: string | null;
  source_record_id: string | null;
  context_hash: string | null;
  title: string;
  summary: string;
  data_json: Record<string, unknown>;
  confidence: string;
  created_at: string;
};

export type MasEvidenceBundleResponse = {
  mas_run_id: string;
  evidence_items: MasEvidenceItem[];
  evidence_pack: Record<string, unknown> | null;
  llm_context: Record<string, unknown> | null;
};

export type MasSynthesisSection = {
  title: string;
  content: string;
  evidence_refs: string[];
};

export type MasSynthesisFinding = {
  finding: string;
  confidence: string;
  evidence_refs: string[];
};

export type MasSynthesisRisk = {
  risk: string;
  severity: string;
  mitigation: string;
  evidence_refs: string[];
};

export type MasSynthesisAction = {
  action: string;
  priority: string;
  evidence_refs: string[];
};

export type MasSynthesisOutput = {
  answer_type: string;
  executive_summary: string;
  final_recommendation: string;
  reasoning_sections: MasSynthesisSection[];
  key_findings: MasSynthesisFinding[];
  risks: MasSynthesisRisk[];
  recommended_next_actions: MasSynthesisAction[];
  evidence_used: Array<{
    evidence_id: string;
    type: string;
    reason_used: string;
  }>;
  limitations: string[];
  confidence: string;
};

export type MasRunDetailResponse = {
  mas_run_id: string;
  project_id: string;
  status: MasRunStatus;
  user_query: string;
  resolved_intent: string | null;
  resolved_context: Record<string, unknown>;
  planner_output_json: Record<string, unknown> | null;
  synthesis_output: MasSynthesisOutput | null;
  final_answer: string | null;
  final_summary: string | null;
  tool_calls: MasToolCall[];
  evidence_items: MasEvidenceItem[];
  evidence_pack: Record<string, unknown> | null;
  llm_context: Record<string, unknown> | null;
  rag_chunks_used: Array<Record<string, unknown>>;
  llm_provider: string | null;
  llm_model: string | null;
  embedding_provider: string | null;
  prompt_version: string | null;
  metrics_json: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};
