import { fetchApi } from '@/lib/api/client';
import type {
  ActionExecution,
  ActionExecutionListResponse,
  ActionResult,
  LearningEventListResponse,
  ModelReviewListResponse,
  OutcomeComparison,
  RecommendationDecision,
} from '@/lib/types/feedback';


export function createDecision(recommendationId: string, decision: string, reasonCategory: string, reasonText: string) {
  return fetchApi<RecommendationDecision>(`/feedback/recommendations/${recommendationId}/decision`, {
    body: JSON.stringify({
      decision,
      reason_category: reasonCategory || 'unknown',
      reason_text: reasonText || null,
      expected_action_json: {},
    }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
}

export function createExpectation(recommendationId: string) {
  return fetchApi(`/feedback/recommendations/${recommendationId}/expectations`, {
    body: JSON.stringify({
      expected_direction: 'directional',
      expected_metric: 'traffic_outcome',
      assumptions_json: { assumptions: ['Recommendation should improve or protect traffic quality.'] },
      confidence: 'medium',
    }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
}

export function compareOutcome(recommendationId: string) {
  return fetchApi<OutcomeComparison>(`/feedback/recommendations/${recommendationId}/compare-outcome`, {
    method: 'POST',
  });
}

export function getActions() {
  return fetchApi<ActionExecutionListResponse>('/feedback/actions?limit=50');
}

export function createAction(recommendationId: string | null, actionType: string, channel: string) {
  return fetchApi<ActionExecution>('/feedback/actions', {
    body: JSON.stringify({
      recommendation_id: recommendationId,
      action_type: actionType,
      channel: channel || null,
      status: 'planned',
      metadata_json: {},
    }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
}

export function createResult(actionId: string, trafficGrowth: number, bounceRate: number) {
  return fetchApi<ActionResult>(`/feedback/actions/${actionId}/results`, {
    body: JSON.stringify({
      traffic_growth: trafficGrowth,
      bounce_rate: bounceRate,
      metadata_json: { source: 'manual_feedback' },
    }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
}

export function getLearningEvents() {
  return fetchApi<LearningEventListResponse>('/feedback/learning-events?limit=50');
}

export function getModelReviews() {
  return fetchApi<ModelReviewListResponse>('/feedback/model-reviews?limit=50');
}
