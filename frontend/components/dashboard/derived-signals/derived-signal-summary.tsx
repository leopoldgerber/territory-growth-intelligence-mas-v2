import type { DerivedSignalSummary } from '@/lib/types/analytics';


const numberFormatter = new Intl.NumberFormat('en-US');

function SummaryValue({
  combinedScopes,
  companyValue,
  competitorValue,
}: {
  combinedScopes: boolean;
  companyValue: number | null;
  competitorValue: number | null;
}) {
  if (combinedScopes) {
    return <span className="text-foreground">{numberFormatter.format(companyValue ?? 0)}</span>;
  }
  return (
    <span className="inline-flex items-center gap-1.5">
      {companyValue !== null ? <span className="text-emerald-500">{numberFormatter.format(companyValue)}</span> : null}
      {companyValue !== null && competitorValue !== null ? <span className="text-muted-foreground">|</span> : null}
      {competitorValue !== null ? <span className="text-sky-500">{numberFormatter.format(competitorValue)}</span> : null}
    </span>
  );
}

export function DerivedSignalSummaryCards({
  combinedScopes,
  companySummary,
  competitorSummary,
}: {
  combinedScopes: boolean;
  companySummary: DerivedSignalSummary | null;
  competitorSummary: DerivedSignalSummary | null;
}) {
  const cards = [
    { label: 'Total Signals', company: companySummary?.total_signals, competitor: competitorSummary?.total_signals },
    { label: 'High Severity', company: companySummary?.by_severity.high, competitor: competitorSummary?.by_severity.high },
    { label: 'Growth Signals', company: companySummary?.by_group.growth, competitor: competitorSummary?.by_group.growth },
    { label: 'Competition Signals', company: companySummary?.by_group.competition, competitor: competitorSummary?.by_group.competition },
    {
      label: 'Quality Signals',
      company: companySummary ? (companySummary.by_group.quality ?? 0) + (companySummary.by_group.device ?? 0) : undefined,
      competitor: competitorSummary ? (competitorSummary.by_group.quality ?? 0) + (competitorSummary.by_group.device ?? 0) : undefined,
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => (
        <div className="rounded-md border bg-background p-4" key={card.label}>
          <p className="text-xs font-medium text-muted-foreground">{card.label}</p>
          <p className="mt-2 text-xl font-semibold">
            <SummaryValue
              combinedScopes={combinedScopes}
              companyValue={companySummary ? card.company ?? 0 : null}
              competitorValue={competitorSummary ? card.competitor ?? 0 : null}
            />
          </p>
        </div>
      ))}
    </div>
  );
}
