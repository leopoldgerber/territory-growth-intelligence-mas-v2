import { InformationPopover } from '@/components/dashboard/information-popover';
import type { OpportunityScoreSummary } from '@/lib/types/analytics';


const numberFormatter = new Intl.NumberFormat('en-US');
const scoreFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });

export function ScoringSummaryCards({ summary }: { summary: OpportunityScoreSummary }) {
  const cards = [
    {
      label: 'Total Countries',
      value: numberFormatter.format(summary.total_countries),
      description: 'Number of distinct countries with persisted scores in the selected scopes.',
    },
    {
      label: 'Average Score',
      value: scoreFormatter.format(summary.average_score),
      description: 'Arithmetic mean of the displayed opportunity scores.',
    },
    {
      label: 'Top Country',
      value: summary.top_country ?? 'None',
      description: 'Country with the highest score; scope ranking rules resolve ties.',
    },
    {
      label: 'Very High / High',
      value: numberFormatter.format((summary.by_category.very_high ?? 0) + (summary.by_category.high ?? 0)),
      description: 'Count of scores in very_high (80-100) or high (65-79.9999) categories.',
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <div className="rounded-md border bg-background p-4" key={card.label}>
          <div className="flex min-h-6 items-center justify-between gap-2">
            <p className="text-xs font-medium text-muted-foreground">{card.label}</p>
            <InformationPopover ariaLabel={`About ${card.label.toLowerCase()}`} title={card.label}>
              {card.description}
            </InformationPopover>
          </div>
          <p className="mt-2 truncate text-xl font-semibold text-foreground">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
