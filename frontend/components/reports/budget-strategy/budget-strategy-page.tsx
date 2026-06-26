'use client';

import { useState } from 'react';

import { BudgetStrategyForm } from './budget-strategy-form';
import { BudgetStrategyReportView } from './budget-strategy-report';
import { SavedStrategiesList } from './saved-strategies-list';

import { InformationPopover } from '@/components/dashboard/information-popover';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useBudgetStrategiesQuery,
  useBudgetStrategyQuery,
  useGenerateBudgetStrategyMutation,
} from '@/lib/api/report-queries';


function read_error(error: unknown): string {
  return error instanceof Error ? error.message : 'Unknown report generation error.';
}

export function BudgetStrategyPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const listQuery = useBudgetStrategiesQuery();
  const reportQuery = useBudgetStrategyQuery(selectedId);
  const generateMutation = useGenerateBudgetStrategyMutation();
  const activeReport = generateMutation.data && selectedId === null ? generateMutation.data : reportQuery.data;

  return (
    <main className="flex w-full flex-1 flex-col px-4 py-6 md:px-6">
      <div className="space-y-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-normal text-foreground">Budget Strategy</h1>
            <InformationPopover ariaLabel="About budget strategy" title="Budget Strategy">
              A rule-based marketing recommendation built from stored analytics. Expected effects are directional and do not predict ROI, CPA, revenue, conversions, or customer counts.
            </InformationPopover>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Generate and save an explainable channel allocation for one country, period, and budget.
          </p>
        </div>

        <BudgetStrategyForm
          isPending={generateMutation.isPending}
          onSubmit={(request) => {
            setSelectedId(null);
            generateMutation.mutate(request);
          }}
        />

        {generateMutation.isError ? <Alert variant="destructive"><AlertTitle>Failed to generate budget strategy.</AlertTitle><AlertDescription>{read_error(generateMutation.error)}</AlertDescription></Alert> : null}
        {generateMutation.isSuccess ? <Alert><AlertTitle>Budget strategy generated.</AlertTitle><AlertDescription>The report was saved and remains available after page refresh.</AlertDescription></Alert> : null}

        {listQuery.isLoading ? <Skeleton className="h-28" /> : null}
        {listQuery.isError ? <Alert variant="destructive"><AlertTitle>Failed to load saved strategies.</AlertTitle></Alert> : null}
        {listQuery.data ? <SavedStrategiesList items={listQuery.data.items} onSelect={setSelectedId} selectedId={selectedId} /> : null}

        {reportQuery.isLoading ? <Skeleton className="h-96" /> : null}
        {reportQuery.isError ? <Alert variant="destructive"><AlertTitle>Failed to load selected strategy.</AlertTitle></Alert> : null}
        {activeReport ? <BudgetStrategyReportView report={activeReport} /> : null}
        {!activeReport && !generateMutation.isPending && selectedId === null ? <Alert><AlertTitle>No strategy selected.</AlertTitle><AlertDescription>Generate a new strategy or open a saved report.</AlertDescription></Alert> : null}
      </div>
    </main>
  );
}
