'use client';

import { RefreshCw } from 'lucide-react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { DerivedSignalSummaryCards } from './derived-signal-summary';
import { DerivedSignalTable } from './derived-signal-table';

import { InformationPopover } from '@/components/dashboard/information-popover';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useDerivedSignalsQuery,
  useDerivedSignalsSummaryQuery,
  useRecalculateDerivedSignalsMutation,
} from '@/lib/api/analytics-queries';


const signalGroups = ['all', 'growth', 'volatility', 'competition', 'territory', 'channel', 'quality', 'device'];
const severities = ['all', 'low', 'medium', 'high', 'critical'];

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

export function DerivedSignalsSection() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const signalGroup = searchParams.get('signalGroup') ?? 'all';
  const severity = searchParams.get('severity') ?? 'all';
  const company = searchParams.get('company') ?? 'all';
  const companyDomain = searchParams.get('companyDomain') ?? 'all';
  const competitors = searchParams.get('competitors') ?? 'all';
  const competitorDomain = searchParams.get('competitorDomain') ?? 'all';
  const combinedScopes = [company, companyDomain, competitors, competitorDomain].every((value) => value === 'all');
  const showCompany = !combinedScopes && company !== 'none';
  const showCompetitors = !combinedScopes && competitors !== 'none';
  const hasSelectedScopes = combinedScopes || showCompany || showCompetitors;
  const overallSignals = useDerivedSignalsQuery('overall', combinedScopes);
  const companySignals = useDerivedSignalsQuery('company', showCompany);
  const competitorSignals = useDerivedSignalsQuery('competitor', showCompetitors);
  const overallSummary = useDerivedSignalsSummaryQuery('overall', combinedScopes);
  const companySummary = useDerivedSignalsSummaryQuery('company', showCompany);
  const competitorSummary = useDerivedSignalsSummaryQuery('competitor', showCompetitors);
  const recalculateMutation = useRecalculateDerivedSignalsMutation();
  const signals = combinedScopes
    ? overallSignals.data ?? []
    : [...(companySignals.data ?? []), ...(competitorSignals.data ?? [])];
  const isLoading = combinedScopes
    ? overallSignals.isLoading || overallSummary.isLoading
    : (showCompany && (companySignals.isLoading || companySummary.isLoading))
      || (showCompetitors && (competitorSignals.isLoading || competitorSummary.isLoading));
  const isError = [
    overallSignals,
    companySignals,
    competitorSignals,
    overallSummary,
    companySummary,
    competitorSummary,
  ].some((query) => query.isError);

  function update_filter(key: 'signalGroup' | 'severity', value: string): void {
    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.set(key, value);
    router.replace(`${pathname}?${nextParams.toString()}`, { scroll: false });
  }

  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold tracking-normal text-foreground">Derived Signals</h2>
              <InformationPopover ariaLabel="About derived signals" title="Derived Signals">
                Explainable analytical facts calculated from traffic, competition, channel, and device data. They are not recommendations, reports, or final scoring.
              </InformationPopover>
            </div>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Persisted observations for unusual growth, competition, territory, channel, and quality patterns.
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
            {recalculateMutation.isPending ? 'Recalculating' : 'Recalculate signals'}
          </Button>
        </div>

        {recalculateMutation.isSuccess ? (
          <Alert>
            <AlertTitle>Signals recalculated.</AlertTitle>
            <AlertDescription>
              {recalculateMutation.data.inserted_count} signals saved; {recalculateMutation.data.deleted_count} previous records replaced.
            </AlertDescription>
          </Alert>
        ) : null}
        {recalculateMutation.isError ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to recalculate signals.</AlertTitle>
            <AlertDescription>Check the backend response and selected dashboard period.</AlertDescription>
          </Alert>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2 lg:max-w-2xl">
          <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
            <span className="flex items-center gap-1">
              Signal group
              <InformationPopover ariaLabel="About signal groups" title="Signal group">
                <p><strong>all:</strong> every signal group.</p>
                <p><strong>growth:</strong> traffic growth, decline, or new activity.</p>
                <p><strong>volatility:</strong> stable or unusually variable daily traffic.</p>
                <p><strong>competition:</strong> concentration, fragmentation, and competitor expansion.</p>
                <p><strong>territory:</strong> new, inactive, or low-noise markets.</p>
                <p><strong>channel:</strong> material acquisition-channel share changes.</p>
                <p><strong>quality:</strong> weaker bounce-rate or visit-duration performance.</p>
                <p><strong>device:</strong> desktop and mobile traffic-quality differences.</p>
              </InformationPopover>
            </span>
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-sm font-normal text-foreground outline-none focus:border-ring focus:ring-2 focus:ring-ring/40"
              onChange={(event) => update_filter('signalGroup', event.target.value)}
              value={signalGroup}
            >
              {signalGroups.map((group) => <option key={group} value={group}>{format_label(group)}</option>)}
            </select>
          </label>
          <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
            <span className="flex items-center gap-1">
              Severity
              <InformationPopover ariaLabel="About signal severity levels" title="Severity">
                <p><strong>all:</strong> every severity level.</p>
                <p><strong>low:</strong> informative or early-stage condition.</p>
                <p><strong>medium:</strong> material condition worth monitoring.</p>
                <p><strong>high:</strong> strong deviation or elevated analytical risk.</p>
                <p><strong>critical:</strong> highest-priority condition when supported by a rule.</p>
              </InformationPopover>
            </span>
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-sm font-normal text-foreground outline-none focus:border-ring focus:ring-2 focus:ring-ring/40"
              onChange={(event) => update_filter('severity', event.target.value)}
              value={severity}
            >
              {severities.map((item) => <option key={item} value={item}>{format_label(item)}</option>)}
            </select>
          </label>
        </div>

        {isLoading ? (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => <Skeleton className="h-24" key={index} />)}
          </div>
        ) : null}
        {!hasSelectedScopes ? (
          <Alert>
            <AlertTitle>Company and competitors are not selected.</AlertTitle>
            <AlertDescription>Select a company or competitors to calculate and display signals.</AlertDescription>
          </Alert>
        ) : null}
        {!isLoading && hasSelectedScopes ? (
          <DerivedSignalSummaryCards
            combinedScopes={combinedScopes}
            companySummary={combinedScopes ? overallSummary.data ?? null : companySummary.data ?? null}
            competitorSummary={combinedScopes ? null : competitorSummary.data ?? null}
          />
        ) : null}

        {isLoading && hasSelectedScopes ? <Skeleton className="h-72" /> : null}
        {isError ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to load derived signals.</AlertTitle>
            <AlertDescription>Check that the backend and derived signal endpoints are available.</AlertDescription>
          </Alert>
        ) : null}
        {hasSelectedScopes && signals.length ? <DerivedSignalTable combinedScopes={combinedScopes} signals={signals} /> : null}
        {!isLoading && hasSelectedScopes && signals.length === 0 ? (
          <Alert>
            <AlertTitle>No derived signals found for selected filters.</AlertTitle>
            <AlertDescription>Use Recalculate signals to calculate and persist this analytical period.</AlertDescription>
          </Alert>
        ) : null}
      </div>
    </section>
  );
}
