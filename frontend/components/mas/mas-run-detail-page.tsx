'use client';

import Link from 'next/link';
import { ArrowLeft, RefreshCw } from 'lucide-react';

import { MasEvidencePanel } from '@/components/mas/mas-evidence-panel';
import { MasRunMetadata } from '@/components/mas/mas-run-metadata';
import { MasRunProgress } from '@/components/mas/mas-run-progress';
import { MasStructuredAnswer } from '@/components/mas/mas-structured-answer';
import { MasWarningsPanel } from '@/components/mas/mas-warnings-panel';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMasRunQuery } from '@/lib/api/mas-queries';


export function MasRunDetailPage({ runId }: { runId: string }) {
  const runQuery = useMasRunQuery(runId);
  const run = runQuery.data ?? null;

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 md:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <Button asChild className="gap-2" variant="ghost">
            <Link href="/mas">
              <ArrowLeft className="h-4 w-4" />
              MAS Analysis
            </Link>
          </Button>
          <h1 className="text-xl font-semibold tracking-normal">Saved MAS Run</h1>
        </div>
        <Button
          className="gap-2"
          disabled={runQuery.isFetching}
          onClick={() => void runQuery.refetch()}
          variant="outline"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>
      {runQuery.isLoading ? (
        <Card>
          <CardHeader>
            <CardTitle>Loading run</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Fetching saved MAS result.</p>
          </CardContent>
        </Card>
      ) : null}
      {runQuery.isError ? (
        <MasWarningsPanel error={runQuery.error instanceof Error ? runQuery.error.message : 'Failed to load MAS run.'} />
      ) : null}
      {run ? (
        <div className="space-y-5">
          <MasWarningsPanel
            error={run.status === 'failed' ? run.error_message : null}
            warnings={run.status === 'partial' ? run.synthesis_output?.limitations ?? [] : []}
          />
          <MasRunMetadata run={run} />
          <MasRunProgress run={run} />
          <MasStructuredAnswer output={run.synthesis_output} />
          <MasEvidencePanel evidenceItems={run.evidence_items} />
        </div>
      ) : null}
    </main>
  );
}
