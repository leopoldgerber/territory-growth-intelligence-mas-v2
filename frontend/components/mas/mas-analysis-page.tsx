'use client';

import Link from 'next/link';
import { useState } from 'react';
import { BrainCircuit, ExternalLink } from 'lucide-react';

import { MasEvidencePanel } from '@/components/mas/mas-evidence-panel';
import { MasRecentRuns } from '@/components/mas/mas-recent-runs';
import { MasRunForm } from '@/components/mas/mas-run-form';
import { MasRunMetadata } from '@/components/mas/mas-run-metadata';
import { MasRunProgress } from '@/components/mas/mas-run-progress';
import { MasStructuredAnswer } from '@/components/mas/mas-structured-answer';
import { MasWarningsPanel } from '@/components/mas/mas-warnings-panel';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreateMasRunMutation, useMasRunQuery, useMasRunsQuery } from '@/lib/api/mas-queries';
import type { MasWorkflowResponse } from '@/lib/types/mas';


export function MasAnalysisPage() {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<MasWorkflowResponse | null>(null);
  const createRun = useCreateMasRunMutation();
  const runQuery = useMasRunQuery(selectedRunId);
  const recentRunsQuery = useMasRunsQuery({ limit: 8 });
  const run = runQuery.data ?? null;
  const pendingWorkflow: MasWorkflowResponse | null = createRun.isPending
    ? buildPendingWorkflow(selectedRunId)
    : workflow;
  const warningItems = [
    ...(workflow?.warnings ?? []),
    ...(run?.synthesis_output?.limitations ?? []),
  ];
  const errorMessage = createRun.error instanceof Error
    ? createRun.error.message
    : run?.error_message;

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 md:px-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-primary" />
            <h1 className="text-xl font-semibold tracking-normal">MAS Analysis</h1>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Run evidence-backed AI-assisted analysis over deterministic analytics, reports, evidence pack, and synthesis.
          </p>
        </div>
        {selectedRunId ? (
          <Button asChild className="gap-2" variant="outline">
            <Link href={`/mas/runs/${selectedRunId}`}>
              <ExternalLink className="h-4 w-4" />
              Open saved run
            </Link>
          </Button>
        ) : null}
      </div>
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-5">
          <Card>
            <CardHeader>
              <CardTitle>Launch MAS Workflow</CardTitle>
            </CardHeader>
            <CardContent>
              <MasRunForm
                isPending={createRun.isPending}
                onSubmit={(request) => {
                  createRun.mutate(request, {
                    onSuccess: (response) => {
                      setWorkflow(response);
                      setSelectedRunId(response.mas_run_id);
                    },
                  });
                }}
              />
            </CardContent>
          </Card>
          <MasWarningsPanel
            error={errorMessage}
            questions={workflow?.clarification_questions}
            warnings={warningItems}
          />
          <MasRunProgress run={run} workflow={pendingWorkflow} />
          <MasStructuredAnswer output={run?.synthesis_output ?? null} />
          <MasEvidencePanel evidenceItems={run?.evidence_items ?? []} />
        </div>
        <aside className="space-y-5">
          <MasRunMetadata run={run} workflow={pendingWorkflow} />
          <MasRecentRuns runs={recentRunsQuery.data?.items ?? []} />
          {recentRunsQuery.isError ? (
            <p className="text-sm text-destructive">Failed to load recent MAS runs.</p>
          ) : null}
        </aside>
      </div>
    </main>
  );
}

function buildPendingWorkflow(runId: string | null): MasWorkflowResponse {
  return {
    mas_run_id: runId ?? 'pending',
    status: 'running',
    resolved_intent: null,
    resolved_context: {},
    final_answer: null,
    final_summary: null,
    confidence: null,
    evidence_count: 0,
    warnings: [],
    clarification_questions: [],
    error_message: null,
    created_at: new Date().toISOString(),
    completed_at: null,
  };
}
