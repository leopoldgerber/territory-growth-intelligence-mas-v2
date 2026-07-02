'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { AlertTriangle, Bell, CheckCircle2, ExternalLink, RefreshCw, ShieldAlert, TrendingUp } from 'lucide-react';

import { formatDateTime } from '@/components/mas/mas-format';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  useAlertStatusMutation,
  useAlertSummaryQuery,
  useAlertsQuery,
  useDetectAlertsMutation,
  useUpdateStatusQuery,
} from '@/lib/api/alert-queries';
import type { AlertEvent, AlertListParams, AlertSummary, DataFreshnessStatus, RecalculationJob } from '@/lib/types/alerts';


const alertTypes = [
  'traffic_spike',
  'traffic_drop',
  'competitor_new_country',
  'competitor_left_country',
  'channel_spike_paid',
  'channel_spike_referral',
  'channel_spike_social',
  'traffic_quality_drop',
  'market_window',
  'opportunity_score_change',
  'signal_severity_increase',
];

export function AlertsPage() {
  const [alertType, setAlertType] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const params = useMemo<AlertListParams>(() => ({
    alertType: alertType || undefined,
    severity: severity || undefined,
    status: status || undefined,
    limit: 40,
  }), [alertType, severity, status]);
  const alertsQuery = useAlertsQuery(params);
  const summaryQuery = useAlertSummaryQuery(params);
  const updateQuery = useUpdateStatusQuery();
  const detectMutation = useDetectAlertsMutation();
  const statusMutation = useAlertStatusMutation();
  const alerts = alertsQuery.data?.items ?? [];

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 md:px-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary" />
            <h1 className="text-xl font-semibold tracking-normal">Alerts</h1>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Proactive market intelligence from data updates, recalculated signals, opportunity scores, and alert rules.
          </p>
        </div>
        <Button
          className="gap-2"
          disabled={detectMutation.isPending}
          onClick={() => detectMutation.mutate()}
          type="button"
        >
          <RefreshCw className={`h-4 w-4 ${detectMutation.isPending ? 'animate-spin' : ''}`} />
          Detect alerts
        </Button>
      </div>
      {detectMutation.error instanceof Error ? (
        <Alert variant="destructive">
          <AlertTitle>Alert detection failed</AlertTitle>
          <AlertDescription>{detectMutation.error.message}</AlertDescription>
        </Alert>
      ) : null}
      {detectMutation.data ? (
        <Alert>
          <AlertTitle>Detection completed</AlertTitle>
          <AlertDescription>
            {detectMutation.data.alerts_created} created, {detectMutation.data.alerts_updated} updated.
          </AlertDescription>
        </Alert>
      ) : null}
      <AlertFilters
        alertType={alertType}
        severity={severity}
        status={status}
        onAlertType={setAlertType}
        onSeverity={setSeverity}
        onStatus={setStatus}
      />
      <SummaryCards summary={summaryQuery.data} />
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4" />
              Alert Events
              {typeof alertsQuery.data?.total === 'number' ? <Badge variant="outline">{alertsQuery.data.total}</Badge> : null}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alertsQuery.isLoading ? <p className="text-sm text-muted-foreground">Loading alerts...</p> : null}
            {alertsQuery.isError ? <p className="text-sm text-destructive">Failed to load alerts.</p> : null}
            {!alertsQuery.isLoading && !alertsQuery.isError && alerts.length === 0 ? (
              <p className="text-sm text-muted-foreground">No alerts match the current filters.</p>
            ) : null}
            {alerts.map((alert) => (
              <AlertItem
                alert={alert}
                isPending={statusMutation.isPending}
                key={alert.id}
                onStatus={(nextStatus) => statusMutation.mutate({ alertId: alert.id, status: nextStatus })}
              />
            ))}
          </CardContent>
        </Card>
        <aside className="space-y-5">
          <FreshnessCard items={updateQuery.data?.freshness ?? []} />
          <JobsCard items={updateQuery.data?.latest_jobs ?? []} />
        </aside>
      </div>
    </main>
  );
}

function AlertFilters({
  alertType,
  severity,
  status,
  onAlertType,
  onSeverity,
  onStatus,
}: {
  alertType: string;
  severity: string;
  status: string;
  onAlertType: (value: string) => void;
  onSeverity: (value: string) => void;
  onStatus: (value: string) => void;
}) {
  return (
    <Card>
      <CardContent className="grid gap-3 p-4 md:grid-cols-3">
        <label className="space-y-1">
          <span className="text-xs font-medium text-muted-foreground">Alert type</span>
          <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => onAlertType(event.target.value)} value={alertType}>
            <option value="">All types</option>
            {alertTypes.map((type) => <option key={type} value={type}>{formatLabel(type)}</option>)}
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-xs font-medium text-muted-foreground">Severity</span>
          <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => onSeverity(event.target.value)} value={severity}>
            <option value="">All severity</option>
            {['low', 'medium', 'high', 'critical'].map((item) => <option key={item} value={item}>{formatLabel(item)}</option>)}
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-xs font-medium text-muted-foreground">Status</span>
          <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" onChange={(event) => onStatus(event.target.value)} value={status}>
            <option value="">All statuses</option>
            {['new', 'seen', 'acknowledged', 'resolved', 'dismissed', 'archived'].map((item) => <option key={item} value={item}>{formatLabel(item)}</option>)}
          </select>
        </label>
      </CardContent>
    </Card>
  );
}

function SummaryCards({ summary }: { summary?: AlertSummary }) {
  const cards = [
    { label: 'New alerts', value: summary?.new_alerts ?? 0, icon: Bell },
    { label: 'High severity', value: summary?.high_severity ?? 0, icon: AlertTriangle },
    { label: 'Market windows', value: summary?.market_windows ?? 0, icon: TrendingUp },
    { label: 'Competitor movements', value: summary?.competitor_movements ?? 0, icon: RefreshCw },
    { label: 'Quality risks', value: summary?.quality_risks ?? 0, icon: ShieldAlert },
  ];
  return (
    <div className="grid gap-3 md:grid-cols-5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.label}>
            <CardContent className="space-y-2 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-medium text-muted-foreground">{card.label}</p>
                <Icon className="h-4 w-4 text-primary" />
              </div>
              <p className="text-2xl font-semibold">{card.value}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function AlertItem({
  alert,
  isPending,
  onStatus,
}: {
  alert: AlertEvent;
  isPending: boolean;
  onStatus: (status: string) => void;
}) {
  return (
    <div className="space-y-3 rounded-md border bg-background p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{formatLabel(alert.alert_type)}</Badge>
        <Badge className={severityClass(alert.severity)} variant="outline">{formatLabel(alert.severity)}</Badge>
        <Badge variant={alert.status === 'new' ? 'warning' : 'outline'}>{formatLabel(alert.status)}</Badge>
        {alert.channel ? <Badge variant="secondary">{formatLabel(alert.channel)}</Badge> : null}
        <span className="text-xs text-muted-foreground">{formatDateTime(alert.detected_at)}</span>
      </div>
      <div className="space-y-1">
        <p className="break-words text-sm font-medium">{alert.title}</p>
        <p className="break-words text-sm leading-6 text-muted-foreground">{alert.summary}</p>
      </div>
      <div className="grid gap-2 text-xs text-muted-foreground md:grid-cols-3">
        <span>Country: {alert.country_id ?? 'All'}</span>
        <span>Company: {alert.company_id ?? alert.competitor_id ?? 'All'}</span>
        <span>Period: {alert.period_from ?? 'N/A'} - {alert.period_to ?? 'N/A'}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button disabled={isPending || alert.status === 'seen'} onClick={() => onStatus('seen')} size="sm" type="button" variant="outline">Seen</Button>
        <Button disabled={isPending || alert.status === 'acknowledged'} onClick={() => onStatus('acknowledged')} size="sm" type="button" variant="outline">Acknowledge</Button>
        <Button disabled={isPending || alert.status === 'resolved'} onClick={() => onStatus('resolved')} size="sm" type="button" variant="outline">Resolve</Button>
        <Button disabled={isPending || alert.status === 'dismissed'} onClick={() => onStatus('dismissed')} size="sm" type="button" variant="outline">Dismiss</Button>
        <Button asChild className="gap-2" size="sm" variant="outline">
          <Link href="/mas">
            <ExternalLink className="h-4 w-4" />
            Run MAS
          </Link>
        </Button>
        <Button asChild size="sm" variant="link">
          <Link href="/history">Open history</Link>
        </Button>
      </div>
      {alert.evidence_refs_json.length ? (
        <div className="rounded-md bg-secondary/40 p-3 text-xs text-muted-foreground">
          Evidence: {alert.evidence_refs_json.map((item) => `${item.source_table ?? 'source'}:${item.source_record_id ?? ''}`).join(', ')}
        </div>
      ) : null}
    </div>
  );
}

function FreshnessCard({ items }: { items: DataFreshnessStatus[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Freshness</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? <p className="text-sm text-muted-foreground">No freshness records yet.</p> : null}
        {items.map((item) => (
          <div className="space-y-1 rounded-md border bg-background p-3" key={item.id}>
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium">{formatLabel(item.dataset_type)}</p>
              <Badge variant={item.freshness_status === 'fresh' ? 'success' : 'outline'}>{formatLabel(item.freshness_status)}</Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Loaded: {item.latest_loaded_date ?? 'N/A'} · lag: {item.lag_days ?? 0} days
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function JobsCard({ items }: { items: RecalculationJob[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recalculation Jobs</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? <p className="text-sm text-muted-foreground">No recalculation jobs yet.</p> : null}
        {items.map((item) => (
          <div className="space-y-1 rounded-md border bg-background p-3" key={item.id}>
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium">{formatLabel(item.job_type)}</p>
              <Badge variant={item.status === 'completed' ? 'success' : 'outline'}>{formatLabel(item.status)}</Badge>
            </div>
            <p className="text-xs text-muted-foreground">{formatDateTime(item.started_at)}</p>
            {item.error_message ? <p className="text-xs text-destructive">{item.error_message}</p> : null}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function formatLabel(value: string) {
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function severityClass(value: string) {
  if (value === 'critical' || value === 'high') {
    return 'border-destructive/40 text-destructive';
  }
  if (value === 'medium') {
    return 'border-accent/40 text-accent';
  }
  return '';
}
