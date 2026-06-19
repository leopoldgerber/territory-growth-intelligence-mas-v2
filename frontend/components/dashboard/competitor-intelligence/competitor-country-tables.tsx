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
                <th className="px-3 py-2 text-right font-medium">Growth Rate</th>
                <th className="px-3 py-2 text-right font-medium">Status</th>
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
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
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
