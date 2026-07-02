import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  compareOutcome,
  createAction,
  createDecision,
  createExpectation,
  createResult,
  getActions,
  getLearningEvents,
  getModelReviews,
} from '@/lib/api/feedback';


export function useActionsQuery() {
  return useQuery({
    queryKey: ['feedback-actions'],
    queryFn: getActions,
  });
}

export function useLearningQuery() {
  return useQuery({
    queryKey: ['feedback-learning-events'],
    queryFn: getLearningEvents,
  });
}

export function useReviewsQuery() {
  return useQuery({
    queryKey: ['feedback-model-reviews'],
    queryFn: getModelReviews,
  });
}

export function useDecisionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: { recommendationId: string; decision: string; reasonCategory: string; reasonText: string }) => (
      createDecision(request.recommendationId, request.decision, request.reasonCategory, request.reasonText)
    ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['history', 'recommendations'] });
      await queryClient.invalidateQueries({ queryKey: ['feedback-learning-events'] });
    },
  });
}

export function useExpectationMutation() {
  return useMutation({
    mutationFn: (recommendationId: string) => createExpectation(recommendationId),
  });
}

export function useActionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: { recommendationId: string | null; actionType: string; channel: string }) => (
      createAction(request.recommendationId, request.actionType, request.channel)
    ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['feedback-actions'] });
    },
  });
}

export function useResultMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: { actionId: string; trafficGrowth: number; bounceRate: number }) => (
      createResult(request.actionId, request.trafficGrowth, request.bounceRate)
    ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['feedback-actions'] });
    },
  });
}

export function useCompareMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recommendationId: string) => compareOutcome(recommendationId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['feedback-learning-events'] });
      await queryClient.invalidateQueries({ queryKey: ['feedback-model-reviews'] });
      await queryClient.invalidateQueries({ queryKey: ['history', 'recommendations'] });
    },
  });
}
