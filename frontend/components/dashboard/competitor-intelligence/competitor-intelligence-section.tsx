'use client';

import { CompetitorCountryTable, CompetitorMovementTable } from './competitor-country-tables';
import { CompetitorMarketAnalysis } from './competitor-market-analysis';
import { CompetitorSummaryCards } from './competitor-summary-cards';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useCompetitorIntelligenceQuery } from '@/lib/api/analytics-queries';

function LoadingState() {
  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-4">
        <Skeleton className="h-6 w-64" />
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

function EmptySection({ description, title }: { description: string; title: string }) {
  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-4">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold tracking-normal text-foreground">Competitor Intelligence</h2>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Competitor presence, country concentration, growth, stability, and rule-based market signals.
          </p>
        </div>
        <Alert>
          <AlertTitle>{title}</AlertTitle>
          <AlertDescription>{description}</AlertDescription>
        </Alert>
      </div>
    </section>
  );
}

export function CompetitorIntelligenceSection() {
  const competitorIntelligenceQuery = useCompetitorIntelligenceQuery();

  if (competitorIntelligenceQuery.isLoading) {
    return <LoadingState />;
  }

  if (competitorIntelligenceQuery.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Failed to load competitor intelligence.</AlertTitle>
        <AlertDescription>Check that the backend and competitor analytics endpoint are available.</AlertDescription>
      </Alert>
    );
  }

  const data = competitorIntelligenceQuery.data;

  if (!data) {
    return (
      <EmptySection
        description="The analytics response is unavailable."
        title="Competitor intelligence is unavailable."
      />
    );
  }

  if (data.filters.competitors === 'none') {
    return (
      <EmptySection
        description="Choose one or more competitors, or select All to analyze the full competitive set."
        title="Select a competitor or domain to view competitor intelligence."
      />
    );
  }

  if (data.summary.total_traffic === 0) {
    return (
      <EmptySection
        description="Try changing the period, countries, competitors, domains, or top-level domains."
        title="No competitor data found for selected filters."
      />
    );
  }

  const useAccent = data.filters.competitors !== 'all';

  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-5">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold tracking-normal text-foreground">Competitor Intelligence</h2>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Competitor presence, country concentration, growth, stability, and rule-based market signals.
          </p>
        </div>
        <CompetitorSummaryCards data={data} useAccent={useAccent} />
        <CompetitorCountryTable
          countries={data.top_countries}
          emptyMessage="No countries with competitor traffic were found."
          title="Top Countries"
          useAccent={useAccent}
        />
        <div className="grid gap-5 xl:grid-cols-2">
          <CompetitorMovementTable
            countries={data.growing_countries}
            emptyMessage="No growing countries for selected filters."
            title="Growing Countries"
            useAccent={useAccent}
          />
          <CompetitorMovementTable
            countries={data.declining_countries}
            emptyMessage="No declining countries for selected filters."
            title="Declining Countries"
            useAccent={useAccent}
          />
        </div>
        <CompetitorMarketAnalysis data={data} useAccent={useAccent} />
      </div>
    </section>
  );
}
