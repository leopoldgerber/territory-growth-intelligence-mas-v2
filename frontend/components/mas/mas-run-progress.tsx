import { Circle, CircleCheck, CircleDashed, CircleX } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { MasRunDetailResponse, MasRunStatus, MasToolCall, MasWorkflowResponse } from '@/lib/types/mas';


const stages = [
  { key: 'planning', label: 'Planning' },
  { key: 'country_intelligence', label: 'Country Intelligence' },
  { key: 'competitor_intelligence', label: 'Competitor Intelligence' },
  { key: 'channel_intelligence', label: 'Channel Intelligence' },
  { key: 'device_intelligence', label: 'Device Intelligence' },
  { key: 'signals', label: 'Signals' },
  { key: 'opportunity_score', label: 'Opportunity Score' },
  { key: 'budget_strategy', label: 'Budget Strategy' },
  { key: 'rag_retrieval', label: 'RAG Retrieval' },
  { key: 'evidence_pack', label: 'Evidence Pack' },
  { key: 'synthesis', label: 'Synthesis' },
];

export function MasRunProgress({
  run,
  workflow,
}: {
  run?: MasRunDetailResponse | null;
  workflow?: MasWorkflowResponse | null;
}) {
  const toolCalls = run?.tool_calls ?? [];
  const status = run?.status ?? workflow?.status ?? 'pending';
  const stageStatuses = stages.map((stage) => ({
    ...stage,
    status: resolveStage(stage.key, status, toolCalls, run, workflow),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Run Progress</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {stageStatuses.map((stage) => (
            <div className="flex items-center gap-2 rounded-md border bg-background px-3 py-2" key={stage.key}>
              <StageIcon status={stage.status} />
              <span className="min-w-0 flex-1 truncate text-sm">{stage.label}</span>
              <span className={cn('text-xs capitalize', tone(stage.status))}>{stage.status}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function resolveStage(
  key: string,
  runStatus: MasRunStatus,
  toolCalls: MasToolCall[],
  run?: MasRunDetailResponse | null,
  workflow?: MasWorkflowResponse | null,
): MasRunStatus {
  if (key === 'planning') {
    return run?.planner_output_json || workflow?.resolved_intent ? 'completed' : runStatus === 'failed' ? 'failed' : 'pending';
  }
  if (key === 'evidence_pack') {
    return run?.evidence_pack ? 'completed' : terminalStatus(runStatus) ? runStatus : 'pending';
  }
  if (key === 'synthesis') {
    return run?.synthesis_output || workflow?.final_answer ? runStatus === 'partial' ? 'partial' : 'completed' : terminalStatus(runStatus) ? runStatus : 'pending';
  }
  const call = toolCalls.find((item) => item.tool_name === key);
  if (call) {
    return call.status;
  }
  if (runStatus === 'running') {
    return 'pending';
  }
  return terminalStatus(runStatus) ? 'skipped' : 'pending';
}

function terminalStatus(status: MasRunStatus) {
  return ['completed', 'partial', 'failed', 'cancelled', 'skipped', 'needs_clarification'].includes(status);
}

function StageIcon({ status }: { status: MasRunStatus }) {
  if (status === 'completed') {
    return <CircleCheck className="h-4 w-4 text-primary" />;
  }
  if (status === 'failed' || status === 'cancelled') {
    return <CircleX className="h-4 w-4 text-destructive" />;
  }
  if (status === 'partial' || status === 'needs_clarification') {
    return <CircleDashed className="h-4 w-4 text-accent" />;
  }
  return <Circle className="h-4 w-4 text-muted-foreground" />;
}

function tone(status: MasRunStatus) {
  if (status === 'completed') {
    return 'text-primary';
  }
  if (status === 'failed' || status === 'cancelled') {
    return 'text-destructive';
  }
  if (status === 'partial' || status === 'needs_clarification') {
    return 'text-accent';
  }
  return 'text-muted-foreground';
}
