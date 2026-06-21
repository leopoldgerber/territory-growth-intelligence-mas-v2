import { fetchApi } from '@/lib/api/client';
import type {
  BudgetStrategyGenerateRequest,
  BudgetStrategyListResponse,
  BudgetStrategyReport,
} from '@/lib/types/reports';


export function generateBudgetStrategy(request: BudgetStrategyGenerateRequest) {
  return fetchApi<BudgetStrategyReport>('/reports/budget-strategy/generate', {
    body: JSON.stringify(request),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
}

export function getBudgetStrategies() {
  return fetchApi<BudgetStrategyListResponse>('/reports/budget-strategy?limit=50');
}

export function getBudgetStrategy(reportId: number) {
  return fetchApi<BudgetStrategyReport>(`/reports/budget-strategy/${reportId}`);
}
