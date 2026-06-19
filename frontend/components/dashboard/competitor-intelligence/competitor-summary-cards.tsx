import type { CompetitorIntelligenceResponse } from '@/lib/types/analytics';

const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

type CompetitorSummaryCardsProps = {
  data: CompetitorIntelligenceResponse;
  useAccent: boolean;
};

export function CompetitorSummaryCards({ data, useAccent }: CompetitorSummaryCardsProps) {
  const valueClass = useAccent ? 'text-sky-500' : 'text-foreground';
  const cards = [
    {
      label: 'Total Traffic',
      value: numberFormatter.format(data.summary.total_traffic),
    },
    {
      label: 'Active Countries',
      value: numberFormatter.format(data.summary.active_countries),
    },
    {
      label: 'Active Domains',
      value: numberFormatter.format(data.summary.active_domains),
    },
    {
      label: 'Top Country',
      value: data.summary.top_country ?? 'None',
      detail: percentFormatter.format(data.summary.top_country_share),
    },
    {
      label: 'Growth Rate',
      value: percentFormatter.format(data.summary.growth_rate),
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => (
        <div className="rounded-md border bg-background p-4" key={card.label}>
          <p className="text-xs font-medium text-muted-foreground">{card.label}</p>
          <div className="mt-2 flex min-w-0 items-baseline gap-2">
            <p className={`truncate text-xl font-semibold ${valueClass}`}>{card.value}</p>
            {card.detail ? <span className="text-xs text-muted-foreground">{card.detail}</span> : null}
          </div>
        </div>
      ))}
    </div>
  );
}
