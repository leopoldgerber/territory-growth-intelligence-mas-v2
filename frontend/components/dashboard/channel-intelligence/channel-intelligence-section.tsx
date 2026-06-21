'use client';

import { BreakdownCard, ChannelSkewsCard, OpportunitySignalsCard, PaidOrganicCard } from './channel-analysis-cards';
import { ChannelLegend } from './channel-comparison';
import { ChannelMixCard } from './channel-mix-card';
import { ChannelSummaryCards } from './channel-summary-cards';
import { ChannelDependencyTable, TopSourcesTable } from './channel-tables';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useChannelIntelligenceQuery } from '@/lib/api/analytics-queries';
import type { ChannelScopeAnalytics } from '@/lib/types/analytics';


function LoadingState() {
  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-4">
        <Skeleton className="h-6 w-48" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {Array.from({ length: 5 }).map((_, index) => (
            <Skeleton className="h-24" key={index} />
          ))}
        </div>
        <Skeleton className="h-72" />
      </div>
    </section>
  );
}

function has_scope_data(scope: ChannelScopeAnalytics | null): boolean {
  return Boolean(scope && (scope.summary.total_traffic > 0 || scope.top_sources.length > 0));
}

export function ChannelIntelligenceSection() {
  const channelQuery = useChannelIntelligenceQuery();

  if (channelQuery.isLoading) {
    return <LoadingState />;
  }

  if (channelQuery.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Failed to load channel intelligence.</AlertTitle>
        <AlertDescription>Check that the backend and channel analytics endpoint are available.</AlertDescription>
      </Alert>
    );
  }

  const data = channelQuery.data;
  if (!data) {
    return (
      <Alert>
        <AlertTitle>Channel intelligence is unavailable.</AlertTitle>
        <AlertDescription>The analytics response is unavailable.</AlertDescription>
      </Alert>
    );
  }

  const hasData = [data.overall_scope, data.company_scope, data.competitor_scope].some(has_scope_data);
  const companyScope = data.combined_scopes ? data.overall_scope : data.company_scope;
  const comparison = {
    combinedScopes: data.combined_scopes,
    companyScope,
    competitorScope: data.competitor_scope,
  };

  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-5">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold tracking-normal text-foreground">Channels</h2>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Company and competitor channel composition, journey sources, dependencies, and analytical signals.
          </p>
          <ChannelLegend combinedScopes={data.combined_scopes} />
        </div>
        {data.scope_note ? (
          <Alert>
            <AlertTitle>Country-scoped channel analysis</AlertTitle>
            <AlertDescription>{data.scope_note}</AlertDescription>
          </Alert>
        ) : null}
        {!hasData ? (
          <Alert>
            <AlertTitle>No channel data found for selected filters.</AlertTitle>
            <AlertDescription>Try changing the period, countries, companies, domains, or top-level domains.</AlertDescription>
          </Alert>
        ) : null}
        {hasData ? (
          <>
            <ChannelSummaryCards {...comparison} />
            <ChannelMixCard {...comparison} />
            <ChannelDependencyTable {...comparison} />
            <div className="grid gap-4 xl:grid-cols-2">
              <ChannelSkewsCard {...comparison} />
              <OpportunitySignalsCard {...comparison} />
            </div>
            <div className="grid gap-4 lg:grid-cols-3">
              <PaidOrganicCard {...comparison} />
              <BreakdownCard {...comparison} title="Source Type Breakdown" type="source" />
              <BreakdownCard {...comparison} title="Traffic Type Breakdown" type="traffic" />
            </div>
            <TopSourcesTable {...comparison} />
          </>
        ) : null}
      </div>
    </section>
  );
}
