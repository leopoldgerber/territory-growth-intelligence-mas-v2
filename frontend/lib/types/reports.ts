export type BudgetChannelRole = 'priority' | 'test' | 'supporting' | 'risky';
export type StrategyMode = 'existing_presence' | 'market_entry';
export type DependencyStatusValue = 'existing' | 'recalculated' | 'skipped' | 'failed' | 'fallback_used';

export type BudgetAllocationItem = {
  channel: string;
  role: BudgetChannelRole;
  amount: number;
  share: number;
  score: number;
  reason: string;
};

export type StrategyRisk = {
  type: string;
  severity: string;
  message: string;
  affected_channels: string[];
  mitigation_hint: string;
};

export type ExpectedEffect = {
  confidence: string;
  expected_direction: string;
  primary_effects: string[];
  secondary_effects: string[];
  measurement_focus: string[];
};

export type DependencyItemStatus = {
  required: boolean;
  status: DependencyStatusValue;
  contexts: string[];
  used_in_report: boolean;
  is_fallback: boolean;
  score: number | null;
  message: string | null;
};

export type DependencyStatus = {
  signals: DependencyItemStatus;
  opportunity_score: DependencyItemStatus;
  fallbacks_used: string[];
};

export type BudgetStrategyReport = {
  id: number;
  country: string;
  country_code: string;
  date_from: string;
  date_to: string;
  budget_amount: number;
  currency: string;
  strategy_mode: StrategyMode;
  scope: string;
  status: string;
  opportunity_score: number | null;
  recommended_approach: string;
  allocation: BudgetAllocationItem[];
  channel_roles: Record<BudgetChannelRole, string[]>;
  expected_effect: ExpectedEffect;
  risks: StrategyRisk[];
  explanation: Record<string, unknown> & { warnings?: string[] };
  dependency_status: DependencyStatus;
  context_hash: string;
  context_json: Record<string, unknown>;
  source_snapshot: Record<string, unknown>;
  calculation_version: string;
  created_at: string;
};

export type BudgetStrategyGenerateRequest = {
  strategy_mode: StrategyMode;
  auto_prepare_dependencies: boolean;
  date_from: string;
  date_to: string;
  country: string;
  budget_amount: number;
  currency: 'USD' | 'EUR';
  company: string;
  company_domain: string;
  competitors: string;
  competitor_domain: string;
  tld: string;
  calculation_version: string;
};

export type BudgetStrategyListResponse = {
  items: BudgetStrategyReport[];
};
