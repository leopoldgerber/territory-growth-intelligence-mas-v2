import { InformationPopover } from '@/components/dashboard/information-popover';

import { DeviceComparisonValue, type DeviceComparisonProps } from './device-comparison';


const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

function format_label(value: string | null): string {
  if (!value) {
    return 'None';
  }
  return value.replace(/^./, (character) => character.toUpperCase());
}

export function DeviceSummaryCards({ combinedScopes, companyScope, competitorScope }: DeviceComparisonProps) {
  const company = companyScope?.summary;
  const competitor = competitorScope?.summary;
  const cards = [
    {
      label: 'Total Visits',
      companyValue: company ? numberFormatter.format(company.visits_total) : null,
      competitorValue: competitor ? numberFormatter.format(competitor.visits_total) : null,
    },
    {
      label: 'Desktop Visits',
      deviceClass: 'bg-[#FB7185]',
      companyValue: company ? numberFormatter.format(company.desktop_visits) : null,
      competitorValue: competitor ? numberFormatter.format(competitor.desktop_visits) : null,
    },
    {
      label: 'Mobile Visits',
      deviceClass: 'bg-[#FDBA74]',
      companyValue: company ? numberFormatter.format(company.mobile_visits) : null,
      competitorValue: competitor ? numberFormatter.format(competitor.mobile_visits) : null,
    },
    {
      label: 'Desktop Share',
      deviceClass: 'bg-[#FB7185]',
      companyValue: company ? percentFormatter.format(company.desktop_share) : null,
      competitorValue: competitor ? percentFormatter.format(competitor.desktop_share) : null,
    },
    {
      label: 'Mobile Share',
      deviceClass: 'bg-[#FDBA74]',
      companyValue: company ? percentFormatter.format(company.mobile_share) : null,
      competitorValue: competitor ? percentFormatter.format(competitor.mobile_share) : null,
    },
    {
      label: 'Dominant Device',
      description: (
        <>
          <p><strong>Desktop:</strong> desktop visits are greater than or equal to mobile visits.</p>
          <p><strong>Mobile:</strong> mobile visits are greater than desktop visits.</p>
          <p><strong>None:</strong> no visits are available.</p>
        </>
      ),
      companyValue: company ? format_label(company.dominant_device) : null,
      competitorValue: competitor ? format_label(competitor.dominant_device) : null,
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
      {cards.map((card) => (
        <div className="rounded-md border bg-background p-4" key={card.label}>
          <div className="flex min-h-6 items-center justify-between gap-2">
            <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
              {card.deviceClass ? <span className={`h-2 w-2 rounded-sm ${card.deviceClass}`} /> : null}
              {card.label}
            </p>
            {card.description ? (
              <InformationPopover ariaLabel="About dominant device statuses" title="Dominant Device">
                {card.description}
              </InformationPopover>
            ) : null}
          </div>
          <DeviceComparisonValue
            className="mt-2 text-xl font-semibold"
            combinedScopes={combinedScopes}
            companyValue={card.companyValue}
            competitorValue={card.competitorValue}
          />
        </div>
      ))}
    </div>
  );
}
