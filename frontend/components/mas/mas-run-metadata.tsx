import { CalendarClock, Cpu, Fingerprint } from 'lucide-react';
import type { ReactNode } from 'react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MasStatusBadge } from '@/components/mas/mas-status-badge';
import { formatDateTime, formatStrategy } from '@/components/mas/mas-format';
import type { MasRunDetailResponse, MasWorkflowResponse } from '@/lib/types/mas';


export function MasRunMetadata({
  run,
  workflow,
}: {
  run?: MasRunDetailResponse | null;
  workflow?: MasWorkflowResponse | null;
}) {
  const runId = run?.mas_run_id ?? workflow?.mas_run_id;
  const status = run?.status ?? workflow?.status;
  const context = run?.resolved_context ?? workflow?.resolved_context ?? {};

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Saved Run</CardTitle>
        {status ? <MasStatusBadge status={status} /> : null}
      </CardHeader>
      <CardContent className="grid gap-3 text-sm md:grid-cols-2 xl:grid-cols-4">
        <MetaItem icon={<Fingerprint className="h-4 w-4" />} label="Run ID" value={runId ?? 'Not created'} />
        <MetaItem icon={<CalendarClock className="h-4 w-4" />} label="Created" value={formatDateTime(run?.created_at ?? workflow?.created_at)} />
        <MetaItem icon={<CalendarClock className="h-4 w-4" />} label="Completed" value={formatDateTime(run?.completed_at ?? workflow?.completed_at)} />
        <MetaItem icon={<Cpu className="h-4 w-4" />} label="Provider / Model" value={providerValue(run)} />
        <MetaItem label="Strategy" value={formatStrategy(readText(context.strategy_mode))} />
        <MetaItem label="Country" value={readText(context.country) ?? 'Not set'} />
        <MetaItem label="Company" value={readText(context.company) ?? 'Not set'} />
        <MetaItem label="Confidence" value={run?.synthesis_output?.confidence ?? workflow?.confidence ?? 'Not set'} />
      </CardContent>
    </Card>
  );
}

function MetaItem({
  icon,
  label,
  value,
}: {
  icon?: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-0 rounded-md border bg-background p-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <p className="mt-1 truncate text-sm font-medium">{value}</p>
    </div>
  );
}

function providerValue(run?: MasRunDetailResponse | null) {
  if (!run) {
    return 'Not loaded';
  }
  return `${run.llm_provider ?? 'unknown'} / ${run.llm_model ?? 'unknown'}`;
}

function readText(value: unknown) {
  if (typeof value === 'string') {
    return value;
  }
  return null;
}
