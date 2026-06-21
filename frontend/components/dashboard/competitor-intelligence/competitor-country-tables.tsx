import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';
import type { CompetitorCountryMetric } from '@/lib/types/analytics';

const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

type CountryTableProps = {
  countries: CompetitorCountryMetric[];
  emptyMessage: string;
  title: string;
  useAccent: boolean;
};

function statusVariant(status: string): 'default' | 'secondary' | 'outline' | 'success' | 'warning' {
  if (status === 'growing' || status === 'new_activity') {
    return 'success';
  }
  if (status === 'declining') {
    return 'warning';
  }
  if (status === 'anchor') {
    return 'default';
  }
  return 'secondary';
}

export function CompetitorCountryTable({ countries, emptyMessage, title, useAccent }: CountryTableProps) {
  const valueClass = useAccent ? 'text-sky-500' : 'text-foreground';

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      {countries.length === 0 ? (
        <div className="rounded-md border bg-background p-4 text-sm text-muted-foreground">{emptyMessage}</div>
      ) : (
        <div className="overflow-x-auto rounded-md border bg-background">
          <table className="w-full min-w-[660px] text-sm">
            <thead className="bg-secondary text-muted-foreground">
              <tr>
                <th className="px-3 py-2 text-left font-medium">Rank</th>
                <th className="px-3 py-2 text-left font-medium">Country</th>
                <th className="px-3 py-2 text-right font-medium">Traffic</th>
                <th className="px-3 py-2 text-right font-medium">Traffic Share</th>
                <th className="px-3 py-2 text-right font-medium">
                  <span className="flex items-center justify-end gap-1">
                    Growth Rate
                    <InformationPopover ariaLabel="About country growth rate" title="Growth Rate">
                      Compares country traffic in the second half of the selected period with the first half.
                    </InformationPopover>
                  </span>
                </th>
                <th className="px-3 py-2 text-right font-medium">
                  <span className="flex items-center justify-end gap-1">
                    Status
                    <InformationPopover ariaLabel="About country statuses" title="Status">
                      <div className="grid gap-3">
                        <div>
                          <p className="font-medium text-foreground">Traffic movement</p>
                          <p><strong>new_activity:</strong> traffic appears only in the second half.</p>
                          <p><strong>growing:</strong> traffic increased by at least 10%.</p>
                          <p><strong>declining:</strong> traffic decreased by at least 10%.</p>
                          <p><strong>stable:</strong> traffic is present without a 10% movement.</p>
                          <p><strong>no_data:</strong> no traffic is available.</p>
                        </div>
                        <div>
                          <p className="font-medium text-foreground">Market role</p>
                          <p><strong>anchor:</strong> a top-three country or at least 15% of traffic.</p>
                          <p><strong>established:</strong> between 5% and 15% of traffic outside the top three.</p>
                          <p><strong>peripheral:</strong> less than 5% of traffic outside the top three.</p>
                        </div>
                      </div>
                    </InformationPopover>
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {countries.map((country, index) => (
                <tr className="border-t" key={country.country_id}>
                  <td className="px-3 py-2 text-muted-foreground">{index + 1}</td>
                  <td className={`px-3 py-2 font-medium ${valueClass}`}>
                    {country.country} <span className="text-xs text-muted-foreground">{country.country_code}</span>
                  </td>
                  <td className={`px-3 py-2 text-right ${valueClass}`}>
                    {numberFormatter.format(country.traffic)}
                  </td>
                  <td className={`px-3 py-2 text-right ${valueClass}`}>
                    {percentFormatter.format(country.traffic_share)}
                  </td>
                  <td className={`px-3 py-2 text-right ${valueClass}`}>
                    {percentFormatter.format(country.growth_rate)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex justify-end gap-1.5">
                      <Badge variant={statusVariant(country.growth_status)}>{country.growth_status}</Badge>
                      <Badge variant={statusVariant(country.status)}>{country.status}</Badge>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function CompetitorMovementTable({ countries, emptyMessage, title, useAccent }: CountryTableProps) {
  const valueClass = useAccent ? 'text-sky-500' : 'text-foreground';

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <InformationPopover ariaLabel={`About ${title.toLowerCase()}`} title={title}>
          {title === 'Growing Countries'
            ? 'Countries with at least 10% traffic growth, including countries where traffic appeared only in the second half of the period.'
            : 'Countries where traffic declined by at least 10% between the first and second halves of the selected period.'}
        </InformationPopover>
      </div>
      <div className="overflow-hidden rounded-md border bg-background">
        {countries.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">{emptyMessage}</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-secondary text-muted-foreground">
              <tr>
                <th className="px-3 py-2 text-left font-medium">Country</th>
                <th className="px-3 py-2 text-right font-medium">Traffic</th>
                <th className="px-3 py-2 text-right font-medium">Growth</th>
              </tr>
            </thead>
            <tbody>
              {countries.map((country) => (
                <tr className="border-t" key={country.country_id}>
                  <td className={`px-3 py-2 font-medium ${valueClass}`}>{country.country}</td>
                  <td className={`px-3 py-2 text-right ${valueClass}`}>
                    {numberFormatter.format(country.traffic)}
                  </td>
                  <td className={`px-3 py-2 text-right ${valueClass}`}>
                    {percentFormatter.format(country.growth_rate)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
