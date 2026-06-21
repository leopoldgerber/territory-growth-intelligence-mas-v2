'use client';

import { RefreshCw } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';

import { ScoringDetail, ScoringRankingTable } from './scoring-ranking';
import { ScoringSummaryCards } from './scoring-summary-cards';

import { InformationPopover } from '@/components/dashboard/information-popover';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useOpportunityScoresQuery,
  useOpportunityScoringSummaryQuery,
  useRecalculateOpportunityScoresMutation,
} from '@/lib/api/analytics-queries';
import type { OpportunityScore, OpportunityScoreSummary } from '@/lib/types/analytics';


function combine_summaries(summaries: OpportunityScoreSummary[], items: OpportunityScore[]): OpportunityScoreSummary {
  if (summaries.length === 0) {
    return { total_countries: 0, average_score: 0, top_country: null, top_score: 0, by_category: {} };
  }
  const totalRecords = items.length;
  const topSummary = summaries.reduce((top, summary) => summary.top_score > top.top_score ? summary : top);
  const byCategory: OpportunityScoreSummary['by_category'] = {};
  for (const summary of summaries) {
    for (const [category, count] of Object.entries(summary.by_category)) {
      const categoryKey = category as keyof typeof byCategory;
      byCategory[categoryKey] = (byCategory[categoryKey] ?? 0) + count;
    }
  }
  return {
    total_countries: new Set(items.map((item) => item.country_id)).size,
    average_score: totalRecords
      ? summaries.reduce((total, summary) => total + summary.average_score * summary.total_countries, 0) / totalRecords
      : 0,
    top_country: topSummary.top_country,
    top_score: topSummary.top_score,
    by_category: byCategory,
  };
}

export function OpportunityScoringSection() {
  const searchParams = useSearchParams();
  const [selectedKey, setSelectedKey] = useState('');
  const company = searchParams.get('company') ?? 'all';
  const companyDomain = searchParams.get('companyDomain') ?? 'all';
  const competitors = searchParams.get('competitors') ?? 'all';
  const competitorDomain = searchParams.get('competitorDomain') ?? 'all';
  const combinedScopes = [company, companyDomain, competitors, competitorDomain].every((value) => value === 'all');
  const showCompany = !combinedScopes && company !== 'none';
  const showCompetitors = !combinedScopes && competitors !== 'none';
  const hasSelectedScopes = combinedScopes || showCompany || showCompetitors;
  const overallScores = useOpportunityScoresQuery('overall', combinedScopes);
  const companyScores = useOpportunityScoresQuery('company', showCompany);
  const competitorScores = useOpportunityScoresQuery('competitor', showCompetitors);
  const overallSummary = useOpportunityScoringSummaryQuery('overall', combinedScopes);
  const companySummary = useOpportunityScoringSummaryQuery('company', showCompany);
  const competitorSummary = useOpportunityScoringSummaryQuery('competitor', showCompetitors);
  const recalculateMutation = useRecalculateOpportunityScoresMutation();
  const items = combinedScopes
    ? overallScores.data?.items ?? []
    : [...(companyScores.data?.items ?? []), ...(competitorScores.data?.items ?? [])];
  const summaries = combinedScopes
    ? overallSummary.data ? [overallSummary.data] : []
    : [companySummary.data, competitorSummary.data].filter((summary): summary is OpportunityScoreSummary => Boolean(summary));
  const summary = combine_summaries(summaries, items);
  const isLoading = combinedScopes
    ? overallScores.isLoading || overallSummary.isLoading
    : (showCompany && (companyScores.isLoading || companySummary.isLoading))
      || (showCompetitors && (competitorScores.isLoading || competitorSummary.isLoading));
  const isError = [overallScores, companyScores, competitorScores, overallSummary, companySummary, competitorSummary]
    .some((query) => query.isError);
  const activeKey = selectedKey && items.some((item) => `${item.scope}-${item.country_id}` === selectedKey)
    ? selectedKey
    : items[0] ? `${items[0].scope}-${items[0].country_id}` : '';
  const selectedItem = items.find((item) => `${item.scope}-${item.country_id}` === activeKey) as OpportunityScore | undefined;
  const note = recalculateMutation.data?.note
    ?? overallScores.data?.note
    ?? companyScores.data?.note
    ?? competitorScores.data?.note;

  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold tracking-normal text-foreground">Opportunity Scoring</h2>
              <InformationPopover ariaLabel="About opportunity scoring" title="Opportunity Scoring">
                Score is an explainable analytical indicator based on selected metrics. It is not a MAS recommendation, entry strategy, or budget decision.
              </InformationPopover>
            </div>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Explainable country-level attractiveness score based on market size, growth, quality, competition, risks, and derived signals.
            </p>
            {!combinedScopes ? (
              <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                {showCompany ? <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-emerald-500" /> Company</span> : null}
                {showCompetitors ? <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-sky-500" /> Competitors</span> : null}
              </div>
            ) : null}
          </div>
          <Button
            disabled={recalculateMutation.isPending || !hasSelectedScopes}
            onClick={() => recalculateMutation.mutate()}
            type="button"
          >
            <RefreshCw className={`h-4 w-4 ${recalculateMutation.isPending ? 'animate-spin' : ''}`} />
            {recalculateMutation.isPending ? 'Recalculating' : 'Recalculate scores'}
          </Button>
        </div>

        {!hasSelectedScopes ? (
          <Alert>
            <AlertTitle>Company and competitors are not selected.</AlertTitle>
            <AlertDescription>Select a company or competitors to calculate opportunity scores.</AlertDescription>
          </Alert>
        ) : null}
        {recalculateMutation.isSuccess ? (
          <Alert>
            <AlertTitle>Opportunity scores recalculated.</AlertTitle>
            <AlertDescription>
              {recalculateMutation.data.scores_created} scores saved; {recalculateMutation.data.scores_updated} previous records replaced.
            </AlertDescription>
          </Alert>
        ) : null}
        {recalculateMutation.isError ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to recalculate opportunity scores.</AlertTitle>
            <AlertDescription>Check the backend response, migration state, and selected Dashboard period.</AlertDescription>
          </Alert>
        ) : null}
        {note ? (
          <Alert>
            <AlertTitle>Scoring fallback is active.</AlertTitle>
            <AlertDescription>{note}</AlertDescription>
          </Alert>
        ) : null}
        {isError ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to load opportunity scores.</AlertTitle>
            <AlertDescription>Check that the scoring endpoints and database migration are available.</AlertDescription>
          </Alert>
        ) : null}
        {isLoading ? (
          <>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {Array.from({ length: 4 }).map((_, index) => <Skeleton className="h-24" key={index} />)}
            </div>
            <Skeleton className="h-72" />
          </>
        ) : null}
        {!isLoading && hasSelectedScopes && items.length === 0 ? (
          <Alert>
            <AlertTitle>No opportunity scores found for selected filters.</AlertTitle>
            <AlertDescription>Recalculate scores to generate an explainable country ranking.</AlertDescription>
          </Alert>
        ) : null}
        {!isLoading && items.length > 0 ? (
          <>
            <ScoringSummaryCards summary={summary} />
            <ScoringRankingTable items={items} onSelect={setSelectedKey} selectedKey={activeKey} />
            {selectedItem ? <ScoringDetail item={selectedItem} /> : null}
          </>
        ) : null}
      </div>
    </section>
  );
}
