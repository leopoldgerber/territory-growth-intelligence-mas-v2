'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import { Archive, ExternalLink, FileText, Lightbulb, ListChecks, Search } from 'lucide-react';

import { formatDateTime, formatStrategy } from '@/components/mas/mas-format';
import { MasStatusBadge } from '@/components/mas/mas-status-badge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  useHistoryInsightsQuery,
  useHistoryMasRunsQuery,
  useHistoryRecommendationsQuery,
  useHistoryReportsQuery,
  useUpdateRecommendationMutation,
} from '@/lib/api/history-queries';
import type { HistoryListParams, Insight, Recommendation, ReportSnapshot } from '@/lib/types/history';
import type { MasRunSummary } from '@/lib/types/mas';


type HistoryTab = 'mas-runs' | 'reports' | 'insights' | 'recommendations';

const tabs: Array<{ label: string; value: HistoryTab }> = [
  { label: 'MAS Runs', value: 'mas-runs' },
  { label: 'Reports', value: 'reports' },
  { label: 'Insights', value: 'insights' },
  { label: 'Recommendations', value: 'recommendations' },
];

export function HistoryPage() {
  const [activeTab, setActiveTab] = useState<HistoryTab>('mas-runs');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [strategyMode, setStrategyMode] = useState('');
  const params = useMemo<HistoryListParams>(() => ({
    search: search.trim() || undefined,
    status: status || undefined,
    strategyMode: strategyMode || undefined,
    limit: 25,
  }), [search, status, strategyMode]);

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 md:px-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Archive className="h-5 w-5 text-primary" />
            <h1 className="text-xl font-semibold tracking-normal">History Library</h1>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Review saved MAS runs, generated reports, extracted insights, and actionable recommendations.
          </p>
        </div>
      </div>
      <HistoryFilters
        search={search}
        status={status}
        strategyMode={strategyMode}
        onSearch={setSearch}
        onStatus={setStatus}
        onStrategyMode={setStrategyMode}
      />
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
      {activeTab === 'mas-runs' ? <MasRunsTab params={params} /> : null}
      {activeTab === 'reports' ? <ReportsTab params={params} /> : null}
      {activeTab === 'insights' ? <InsightsTab params={params} /> : null}
      {activeTab === 'recommendations' ? <RecommendationsTab params={params} /> : null}
    </main>
  );
}

function HistoryFilters({
  search,
  status,
  strategyMode,
  onSearch,
  onStatus,
  onStrategyMode,
}: {
  search: string;
  status: string;
  strategyMode: string;
  onSearch: (value: string) => void;
  onStatus: (value: string) => void;
  onStrategyMode: (value: string) => void;
}) {
  return (
    <Card>
      <CardContent className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_220px_220px]">
        <label className="space-y-1">
          <span className="text-xs font-medium text-muted-foreground">Search</span>
          <div className="flex h-9 items-center gap-2 rounded-md border bg-background px-3">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              onChange={(event) => onSearch(event.target.value)}
              placeholder="Search reports, insights, recommendations"
              value={search}
            />
          </div>
        </label>
        <label className="space-y-1">
          <span className="text-xs font-medium text-muted-foreground">Status</span>
          <select
            className="h-9 w-full rounded-md border bg-background px-3 text-sm outline-none"
            onChange={(event) => onStatus(event.target.value)}
            value={status}
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="proposed">Proposed</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
            <option value="completed">Completed</option>
            <option value="superseded">Superseded</option>
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-xs font-medium text-muted-foreground">Strategy mode</span>
          <select
            className="h-9 w-full rounded-md border bg-background px-3 text-sm outline-none"
            onChange={(event) => onStrategyMode(event.target.value)}
            value={strategyMode}
          >
            <option value="">All modes</option>
            <option value="market_entry">Market Entry</option>
            <option value="existing_presence">Existing Presence</option>
          </select>
        </label>
      </CardContent>
    </Card>
  );
}

function MasRunsTab({ params }: { params: HistoryListParams }) {
  const query = useHistoryMasRunsQuery(params);
  const items = query.data?.items ?? [];
  return (
    <HistorySection
      count={query.data?.total}
      emptyText="No historical MAS runs match the current filters."
      error={query.isError}
      icon={<ListChecks className="h-4 w-4" />}
      isLoading={query.isLoading}
      title="MAS Runs"
    >
      {items.map((item) => <MasRunItem item={item} key={item.id} />)}
    </HistorySection>
  );
}

function ReportsTab({ params }: { params: HistoryListParams }) {
  const query = useHistoryReportsQuery(params);
  const items = query.data?.items ?? [];
  return (
    <HistorySection
      count={query.data?.total}
      emptyText="No report snapshots match the current filters."
      error={query.isError}
      icon={<FileText className="h-4 w-4" />}
      isLoading={query.isLoading}
      title="Reports"
    >
      {items.map((item) => <ReportItem item={item} key={item.id} />)}
    </HistorySection>
  );
}

function InsightsTab({ params }: { params: HistoryListParams }) {
  const query = useHistoryInsightsQuery(params);
  const items = query.data?.items ?? [];
  return (
    <HistorySection
      count={query.data?.total}
      emptyText="No extracted insights match the current filters."
      error={query.isError}
      icon={<Lightbulb className="h-4 w-4" />}
      isLoading={query.isLoading}
      title="Insights"
    >
      {items.map((item) => <InsightItem item={item} key={item.id} />)}
    </HistorySection>
  );
}

function RecommendationsTab({ params }: { params: HistoryListParams }) {
  const query = useHistoryRecommendationsQuery(params);
  const mutation = useUpdateRecommendationMutation();
  const items = query.data?.items ?? [];
  return (
    <HistorySection
      count={query.data?.total}
      emptyText="No recommendations match the current filters."
      error={query.isError}
      icon={<ListChecks className="h-4 w-4" />}
      isLoading={query.isLoading}
      title="Recommendations"
    >
      {items.map((item) => (
        <RecommendationItem
          isPending={mutation.isPending}
          item={item}
          key={item.id}
          onStatus={(status) => mutation.mutate({ recommendationId: item.id, status, userDecision: status })}
        />
      ))}
    </HistorySection>
  );
}

function HistorySection({
  children,
  count,
  emptyText,
  error,
  icon,
  isLoading,
  title,
}: {
  children: ReactNode;
  count?: number;
  emptyText: string;
  error: boolean;
  icon: ReactNode;
  isLoading: boolean;
  title: string;
}) {
  const hasItems = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {icon}
          {title}
          {typeof count === 'number' ? <Badge variant="outline">{count}</Badge> : null}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? <p className="text-sm text-muted-foreground">Loading history...</p> : null}
        {error ? <p className="text-sm text-destructive">Failed to load history records.</p> : null}
        {!isLoading && !error && !hasItems ? <p className="text-sm text-muted-foreground">{emptyText}</p> : null}
        {!isLoading && !error ? children : null}
      </CardContent>
    </Card>
  );
}

function MasRunItem({ item }: { item: MasRunSummary }) {
  return (
    <div className="grid gap-3 rounded-md border bg-background p-4 md:grid-cols-[minmax(0,1fr)_auto]">
      <div className="min-w-0 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <MasStatusBadge status={item.status} />
          <Badge variant="outline">{formatStrategy(item.strategy_mode)}</Badge>
          <span className="text-xs text-muted-foreground">{formatDateTime(item.created_at)}</span>
        </div>
        <p className="break-words text-sm font-medium">{item.final_summary || item.user_query}</p>
        <p className="text-xs text-muted-foreground">{item.country ?? 'No country'} · {item.company ?? 'No company'}</p>
      </div>
      <Button asChild className="gap-2" size="sm" variant="outline">
        <Link href={`/mas/runs/${item.id}`}>
          <ExternalLink className="h-4 w-4" />
          Open
        </Link>
      </Button>
    </div>
  );
}

function ReportItem({ item }: { item: ReportSnapshot }) {
  return (
    <div className="space-y-2 rounded-md border bg-background p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{formatType(item.report_type)}</Badge>
        <Badge variant="outline">{item.status}</Badge>
        <span className="text-xs text-muted-foreground">{formatDateTime(item.created_at)}</span>
      </div>
      <p className="break-words text-sm font-medium">{item.title}</p>
      <p className="break-words text-sm text-muted-foreground">{item.summary}</p>
      {item.mas_run_id ? (
        <Button asChild size="sm" variant="link">
          <Link href={`/mas/runs/${item.mas_run_id}`}>Open MAS run</Link>
        </Button>
      ) : null}
    </div>
  );
}

function InsightItem({ item }: { item: Insight }) {
  return (
    <div className="space-y-2 rounded-md border bg-background p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{formatType(item.insight_type)}</Badge>
        {item.severity ? <Badge variant="warning">{item.severity}</Badge> : null}
        <Badge variant="outline">{item.confidence}</Badge>
        <span className="text-xs text-muted-foreground">{formatDateTime(item.created_at)}</span>
      </div>
      <p className="break-words text-sm font-medium">{item.title}</p>
      <p className="break-words text-sm text-muted-foreground">{item.summary}</p>
      {item.tags.length ? (
        <div className="flex flex-wrap gap-1">
          {item.tags.slice(0, 6).map((tag) => <Badge key={tag} variant="secondary">{tag}</Badge>)}
        </div>
      ) : null}
    </div>
  );
}

function RecommendationItem({
  isPending,
  item,
  onStatus,
}: {
  isPending: boolean;
  item: Recommendation;
  onStatus: (status: string) => void;
}) {
  return (
    <div className="space-y-3 rounded-md border bg-background p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{formatType(item.recommendation_type)}</Badge>
        <Badge variant={item.status === 'proposed' ? 'warning' : 'outline'}>{item.status}</Badge>
        <Badge variant="outline">{item.priority}</Badge>
        <span className="text-xs text-muted-foreground">{formatDateTime(item.created_at)}</span>
      </div>
      <div className="space-y-1">
        <p className="break-words text-sm font-medium">{item.title}</p>
        <p className="break-words text-sm text-muted-foreground">{item.description}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {['accepted', 'rejected', 'in_progress', 'completed', 'archived'].map((status) => (
          <Button
            disabled={isPending || item.status === status}
            key={status}
            onClick={() => onStatus(status)}
            size="sm"
            type="button"
            variant="outline"
          >
            {formatType(status)}
          </Button>
        ))}
      </div>
    </div>
  );
}

function formatType(value: string | null | undefined) {
  if (!value) {
    return 'Not set';
  }
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}
