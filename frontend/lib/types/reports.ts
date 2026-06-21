export type BudgetChannelRole = 'priority' | 'test' | 'supporting' | 'risky';

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

export type BudgetStrategyReport = {
  id: number;
  country: string;
  country_code: string;
  date_from: string;
  date_to: string;
  budget_amount: number;
  currency: string;
  scope: string;
  status: string;
  opportunity_score: number | null;
  recommended_approach: string;
  allocation: BudgetAllocationItem[];
  channel_roles: Record<BudgetChannelRole, string[]>;
  expected_effect: ExpectedEffect;
  risks: StrategyRisk[];
  explanation: Record<string, unknown> & { warnings?: string[] };
  source_snapshot: Record<string, unknown>;
  calculation_version: string;
  created_at: string;
};

export type BudgetStrategyGenerateRequest = {
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
