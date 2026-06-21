'use client';

import { DeviceLegend } from './device-comparison';
import { DeviceMetricCards } from './device-metric-cards';
import { DeviceSignalsCard } from './device-signals-card';
import { DeviceSummaryCards } from './device-summary-cards';
import { CompetitorDeviceTable, DeviceTrendTable } from './device-tables';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useDeviceIntelligenceQuery } from '@/lib/api/analytics-queries';


function LoadingState() {
  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-4">
        <Skeleton className="h-6 w-48" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton className="h-24" key={index} />
          ))}
        </div>
        <Skeleton className="h-72" />
      </div>
    </section>
  );
}

export function DeviceIntelligenceSection() {
  const deviceQuery = useDeviceIntelligenceQuery();

  if (deviceQuery.isLoading) {
    return <LoadingState />;
  }

  if (deviceQuery.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Failed to load device intelligence.</AlertTitle>
        <AlertDescription>Check that the backend and device analytics endpoint are available.</AlertDescription>
      </Alert>
    );
  }

  const data = deviceQuery.data;
  if (!data) {
    return (
      <Alert>
        <AlertTitle>Device intelligence is unavailable.</AlertTitle>
        <AlertDescription>The analytics response is unavailable.</AlertDescription>
      </Alert>
    );
  }

  const companyScope = data.combined_scopes ? data.overall_scope : data.company_scope;
  const comparison = {
    combinedScopes: data.combined_scopes,
    companyScope,
    competitorScope: data.competitor_scope,
  };
  const hasSelectedScopes = Boolean(companyScope || data.competitor_scope);
  const hasData = [companyScope, data.competitor_scope].some((scope) => scope && scope.summary.visits_total > 0);

  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-5">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold tracking-normal text-foreground">Devices</h2>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Desktop and mobile traffic, audience quality, engagement differences, and neutral device signals.
          </p>
          <DeviceLegend combinedScopes={data.combined_scopes} />
        </div>
        {data.scope_note ? (
          <Alert>
            <AlertTitle>Country-scoped device analysis</AlertTitle>
            <AlertDescription>{data.scope_note}</AlertDescription>
          </Alert>
        ) : null}
        {!hasData ? (
          <Alert>
            <AlertTitle>No device data found for selected filters.</AlertTitle>
            <AlertDescription>Try changing the period, countries, companies, domains, or top-level domains.</AlertDescription>
          </Alert>
        ) : null}
        {hasSelectedScopes ? (
          <>
            <DeviceSummaryCards {...comparison} />
            <DeviceMetricCards {...comparison} />
            <DeviceSignalsCard {...comparison} />
            <DeviceTrendTable {...comparison} />
            <CompetitorDeviceTable {...comparison} />
          </>
        ) : null}
      </div>
    </section>
  );
}
