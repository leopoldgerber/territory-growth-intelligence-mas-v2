'use client';

import type { ReactNode } from 'react';
import { useState } from 'react';
import { Brain, ClipboardCheck, GitCompare, MessageSquareText, PlayCircle } from 'lucide-react';

import { formatDateTime } from '@/components/mas/mas-format';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  useActionMutation,
  useActionsQuery,
  useCompareMutation,
  useDecisionMutation,
  useExpectationMutation,
  useLearningQuery,
  useResultMutation,
  useReviewsQuery,
} from '@/lib/api/feedback-queries';
import { useHistoryRecommendationsQuery } from '@/lib/api/history-queries';
import type { ActionExecution, LearningEvent, ModelReview } from '@/lib/types/feedback';
import type { Recommendation } from '@/lib/types/history';


type FeedbackTab = 'decisions' | 'actions' | 'outcomes' | 'learning' | 'reviews';

const tabs: Array<{ label: string; value: FeedbackTab }> = [
  { label: 'Decisions', value: 'decisions' },
  { label: 'Actions', value: 'actions' },
  { label: 'Outcomes', value: 'outcomes' },
  { label: 'Learning Events', value: 'learning' },
  { label: 'Model Reviews', value: 'reviews' },
];

export function FeedbackPage() {
  const [activeTab, setActiveTab] = useState<FeedbackTab>('decisions');
  const recommendationsQuery = useHistoryRecommendationsQuery({ limit: 50 });
  const actionsQuery = useActionsQuery();
  const learningQuery = useLearningQuery();
  const reviewsQuery = useReviewsQuery();
  const recommendations = recommendationsQuery.data?.items ?? [];
  const actions = actionsQuery.data?.items ?? [];

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 md:px-6">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <MessageSquareText className="h-5 w-5 text-primary" />
          <h1 className="text-xl font-semibold tracking-normal">Feedback Loop</h1>
        </div>
        <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
          Convert recommendations into decisions, actions, outcomes, learning events, and reviewable model changes.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <Button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            type="button"
            variant={activeTab === tab.value ? 'default' : 'outline'}
          >
            {tab.label}
          </Button>
        ))}
      </div>
      {activeTab === 'decisions' ? <DecisionsTab recommendations={recommendations} /> : null}
      {activeTab === 'actions' ? <ActionsTab actions={actions} recommendations={recommendations} /> : null}
      {activeTab === 'outcomes' ? <OutcomesTab actions={actions} recommendations={recommendations} /> : null}
      {activeTab === 'learning' ? <LearningTab items={learningQuery.data?.items ?? []} /> : null}
      {activeTab === 'reviews' ? <ReviewsTab items={reviewsQuery.data?.items ?? []} /> : null}
    </main>
  );
}

function DecisionsTab({ recommendations }: { recommendations: Recommendation[] }) {
  const [reasonText, setReasonText] = useState('');
  const [reasonCategory, setReasonCategory] = useState('good_fit');
  const decisionMutation = useDecisionMutation();
  const expectationMutation = useExpectationMutation();
  const pending = decisionMutation.isPending || expectationMutation.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardCheck className="h-4 w-4" />
          Recommendation Decisions
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-[220px_minmax(0,1fr)]">
          <label className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground">Reason category</span>
            <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => setReasonCategory(event.target.value)} value={reasonCategory}>
              {['good_fit', 'budget_constraints', 'low_confidence', 'market_risk', 'strategic_mismatch', 'missing_data', 'timing_issue', 'already_planned', 'other'].map((item) => (
                <option key={item} value={item}>{formatLabel(item)}</option>
              ))}
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground">Reason text</span>
            <input className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => setReasonText(event.target.value)} placeholder="Optional decision context" value={reasonText} />
          </label>
        </div>
        {decisionMutation.error instanceof Error ? <ErrorAlert message={decisionMutation.error.message} /> : null}
        {recommendations.length === 0 ? <p className="text-sm text-muted-foreground">No recommendations available yet.</p> : null}
        {recommendations.map((recommendation) => (
          <RecommendationCard key={recommendation.id} recommendation={recommendation}>
            <Button disabled={pending} onClick={() => {
              expectationMutation.mutate(recommendation.id);
              decisionMutation.mutate({ recommendationId: recommendation.id, decision: 'accepted', reasonCategory, reasonText });
            }} size="sm" type="button">
              Accept
            </Button>
            <Button disabled={pending} onClick={() => decisionMutation.mutate({ recommendationId: recommendation.id, decision: 'rejected', reasonCategory, reasonText })} size="sm" type="button" variant="outline">
              Reject
            </Button>
            <Button disabled={pending} onClick={() => decisionMutation.mutate({ recommendationId: recommendation.id, decision: 'deferred', reasonCategory: 'timing_issue', reasonText })} size="sm" type="button" variant="outline">
              Defer
            </Button>
          </RecommendationCard>
        ))}
      </CardContent>
    </Card>
  );
}

function ActionsTab({
  actions,
  recommendations,
}: {
  actions: ActionExecution[];
  recommendations: Recommendation[];
}) {
  const [recommendationId, setRecommendationId] = useState(recommendations[0]?.id ?? '');
  const [actionType, setActionType] = useState('market_entry_test');
  const [channel, setChannel] = useState('');
  const actionMutation = useActionMutation();

  return (
    <div className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle>Create Action</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground">Recommendation</span>
            <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => setRecommendationId(event.target.value)} value={recommendationId}>
              <option value="">No recommendation</option>
              {recommendations.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground">Action type</span>
            <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => setActionType(event.target.value)} value={actionType}>
              {['market_entry_test', 'channel_test', 'budget_reallocation', 'seo_push', 'paid_test', 'referral_partnership', 'competitor_monitoring', 'risk_monitoring'].map((item) => (
                <option key={item} value={item}>{formatLabel(item)}</option>
              ))}
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground">Channel</span>
            <input className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => setChannel(event.target.value)} placeholder="paid, search, referral..." value={channel} />
          </label>
          {actionMutation.error instanceof Error ? <ErrorAlert message={actionMutation.error.message} /> : null}
          <Button disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ recommendationId: recommendationId || null, actionType, channel })} type="button">
            Create action
          </Button>
        </CardContent>
      </Card>
      <ActionList actions={actions} />
    </div>
  );
}

function OutcomesTab({
  actions,
  recommendations,
}: {
  actions: ActionExecution[];
  recommendations: Recommendation[];
}) {
  const [actionId, setActionId] = useState(actions[0]?.id ?? '');
  const [recommendationId, setRecommendationId] = useState(recommendations[0]?.id ?? '');
  const [trafficGrowth, setTrafficGrowth] = useState('0.10');
  const [bounceRate, setBounceRate] = useState('0.35');
  const resultMutation = useResultMutation();
  const compareMutation = useCompareMutation();

  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Add Actual Result</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground">Action</span>
            <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => setActionId(event.target.value)} value={actionId}>
              <option value="">Select action</option>
              {actions.map((item) => <option key={item.id} value={item.id}>{formatLabel(item.action_type)} · {formatDateTime(item.created_at)}</option>)}
            </select>
          </label>
          <div className="grid gap-3 md:grid-cols-2">
            <NumberField label="Traffic growth" onChange={setTrafficGrowth} value={trafficGrowth} />
            <NumberField label="Bounce rate" onChange={setBounceRate} value={bounceRate} />
          </div>
          {resultMutation.error instanceof Error ? <ErrorAlert message={resultMutation.error.message} /> : null}
          <Button disabled={resultMutation.isPending || !actionId} onClick={() => resultMutation.mutate({ actionId, trafficGrowth: Number(trafficGrowth), bounceRate: Number(bounceRate) })} type="button">
            Add result
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="h-4 w-4" />
            Compare Outcome
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground">Recommendation</span>
            <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => setRecommendationId(event.target.value)} value={recommendationId}>
              <option value="">Select recommendation</option>
              {recommendations.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
            </select>
          </label>
          {compareMutation.error instanceof Error ? <ErrorAlert message={compareMutation.error.message} /> : null}
          {compareMutation.data ? (
            <Alert>
              <AlertTitle>{formatLabel(compareMutation.data.classification)}</AlertTitle>
              <AlertDescription>
                Outcome score: {compareMutation.data.outcome_score.toFixed(2)} · assumptions updated: {compareMutation.data.assumptions_updated}
              </AlertDescription>
            </Alert>
          ) : null}
          <Button disabled={compareMutation.isPending || !recommendationId} onClick={() => compareMutation.mutate(recommendationId)} type="button">
            Compare outcome
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function LearningTab({ items }: { items: LearningEvent[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Brain className="h-4 w-4" />Learning Events</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? <p className="text-sm text-muted-foreground">No learning events yet.</p> : null}
        {items.map((item) => (
          <div className="space-y-2 rounded-md border bg-background p-4" key={item.id}>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{formatLabel(item.learning_type)}</Badge>
              <Badge variant="outline">{formatLabel(item.impact_area)}</Badge>
              <span className="text-xs text-muted-foreground">{formatDateTime(item.created_at)}</span>
            </div>
            <p className="text-sm text-muted-foreground">{item.summary}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ReviewsTab({ items }: { items: ModelReview[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Scoring Model Reviews</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? <p className="text-sm text-muted-foreground">No model review proposals yet.</p> : null}
        {items.map((item) => (
          <div className="space-y-2 rounded-md border bg-background p-4" key={item.id}>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{item.model_name}</Badge>
              <Badge variant="outline">{formatLabel(item.status)}</Badge>
              <span className="text-xs text-muted-foreground">{item.current_version} → {item.proposed_version ?? 'review'}</span>
            </div>
            <p className="text-sm text-muted-foreground">{item.reason}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function RecommendationCard({
  children,
  recommendation,
}: {
  children: ReactNode;
  recommendation: Recommendation;
}) {
  return (
    <div className="space-y-3 rounded-md border bg-background p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{formatLabel(recommendation.recommendation_type)}</Badge>
        <Badge variant="outline">{formatLabel(recommendation.status)}</Badge>
        <Badge variant="secondary">{recommendation.priority}</Badge>
      </div>
      <div className="space-y-1">
        <p className="break-words text-sm font-medium">{recommendation.title}</p>
        <p className="break-words text-sm leading-6 text-muted-foreground">{recommendation.description}</p>
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  );
}

function ActionList({ actions }: { actions: ActionExecution[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><PlayCircle className="h-4 w-4" />Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {actions.length === 0 ? <p className="text-sm text-muted-foreground">No tracked actions yet.</p> : null}
        {actions.map((item) => (
          <div className="space-y-2 rounded-md border bg-background p-4" key={item.id}>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{formatLabel(item.action_type)}</Badge>
              <Badge variant="outline">{formatLabel(item.status)}</Badge>
              {item.channel ? <Badge variant="secondary">{item.channel}</Badge> : null}
              <span className="text-xs text-muted-foreground">{formatDateTime(item.created_at)}</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Recommendation: {item.recommendation_id ?? 'None'} · Budget: {item.planned_budget ?? 'N/A'} {item.currency ?? ''}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function NumberField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="space-y-1">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <input className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => onChange(event.target.value)} type="number" value={value} />
    </label>
  );
}

function ErrorAlert({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertTitle>Feedback action failed</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
}

function formatLabel(value: string) {
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}
