import { InformationPopover } from '@/components/dashboard/information-popover';

import { ComparisonValue, type ChannelComparisonProps } from './channel-comparison';

const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

const cardDescriptions: Record<string, string> = {
  'Total Channel Traffic': 'Sum of direct, search, paid, referral, and social traffic in this scope.',
  'Dominant Channel': 'The channel with the highest traffic in this scope.',
  'Dominant Channel Share': 'The dominant channel traffic divided by total channel traffic.',
  'Paid Share': 'Paid journey traffic divided by all classified journey traffic.',
  'Organic Share': 'Organic journey traffic divided by all classified journey traffic.',
};

function format_label(value: string | null): string {
  if (!value) {
    return 'None';
  }
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

export function ChannelSummaryCards({
  combinedScopes,
  companyScope,
  competitorScope,
}: ChannelComparisonProps) {
  const companySummary = companyScope?.summary ?? null;
  const competitorSummary = competitorScope?.summary ?? null;
  const cards = [
    {
      label: 'Total Channel Traffic',
      companyValue: companySummary ? numberFormatter.format(companySummary.total_traffic) : null,
      competitorValue: competitorSummary ? numberFormatter.format(competitorSummary.total_traffic) : null,
      companyDetail: companySummary
        ? `${numberFormatter.format(companySummary.competitors_count)} companies / ${numberFormatter.format(companySummary.domains_count)} domains`
        : null,
      competitorDetail: competitorSummary
        ? `${numberFormatter.format(competitorSummary.competitors_count)} companies / ${numberFormatter.format(competitorSummary.domains_count)} domains`
        : null,
    },
    {
      label: 'Dominant Channel',
      companyValue: companySummary ? format_label(companySummary.dominant_channel) : null,
      competitorValue: competitorSummary ? format_label(competitorSummary.dominant_channel) : null,
    },
    {
      label: 'Dominant Channel Share',
      companyValue: companySummary ? percentFormatter.format(companySummary.dominant_channel_share) : null,
      competitorValue: competitorSummary ? percentFormatter.format(competitorSummary.dominant_channel_share) : null,
    },
    {
      label: 'Paid Share',
      companyValue: companySummary ? percentFormatter.format(companySummary.paid_share) : null,
      competitorValue: competitorSummary ? percentFormatter.format(competitorSummary.paid_share) : null,
    },
    {
      label: 'Organic Share',
      companyValue: companySummary ? percentFormatter.format(companySummary.organic_share) : null,
      competitorValue: competitorSummary ? percentFormatter.format(competitorSummary.organic_share) : null,
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => (
        <div className="rounded-md border bg-background p-4" key={card.label}>
          <div className="flex min-h-6 items-center justify-between gap-2">
            <p className="text-xs font-medium text-muted-foreground">{card.label}</p>
            <InformationPopover ariaLabel={`About ${card.label.toLowerCase()}`} title={card.label}>
              {cardDescriptions[card.label]}
            </InformationPopover>
          </div>
          <ComparisonValue
            className="mt-2 text-xl font-semibold"
            combinedScopes={combinedScopes}
            companyValue={card.companyValue}
            competitorValue={card.competitorValue}
          />
          {card.companyDetail || card.competitorDetail ? (
            <ComparisonValue
              className="mt-1 text-xs"
              combinedScopes={combinedScopes}
              companyValue={card.companyDetail ?? null}
              competitorValue={card.competitorDetail ?? null}
            />
          ) : null}
        </div>
      ))}
    </div>
  );
}
