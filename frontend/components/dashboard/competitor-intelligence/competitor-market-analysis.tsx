import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';
import type { CompetitorCountryMetric, CompetitorIntelligenceResponse } from '@/lib/types/analytics';

const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

type MarketAnalysisProps = {
  data: CompetitorIntelligenceResponse;
  useAccent: boolean;
};

type MarketListProps = {
  countries: CompetitorCountryMetric[];
  emptyMessage: string;
  title: string;
  useAccent: boolean;
};

function analysisVariant(status: string): 'default' | 'secondary' | 'outline' | 'success' | 'warning' {
  if (status === 'stable' || status === 'low') {
    return 'success';
  }
  if (status === 'weak' || status === 'high') {
    return 'warning';
  }
  if (status === 'anchor') {
    return 'default';
  }
  return 'secondary';
}

function MarketList({ countries, emptyMessage, title, useAccent }: MarketListProps) {
  const valueClass = useAccent ? 'text-sky-500' : 'text-foreground';

  return (
    <div className="rounded-md border bg-background p-4">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <InformationPopover ariaLabel={`About ${title.toLowerCase()}`} title={title}>
          {title === 'Anchor Markets'
            ? 'The three highest-traffic countries and any country contributing at least 15% of selected traffic.'
            : 'Countries contributing less than 5% of selected traffic.'}
        </InformationPopover>
      </div>
      {countries.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">{emptyMessage}</p>
      ) : (
        <div className="mt-3 grid gap-2">
          {countries.map((country) => (
            <div className="flex items-center justify-between gap-3 border-b py-2 last:border-b-0" key={country.country_id}>
              <span className={`truncate text-sm font-medium ${valueClass}`}>{country.country}</span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {percentFormatter.format(country.traffic_share)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function CompetitorMarketAnalysis({ data, useAccent }: MarketAnalysisProps) {
  const valueClass = useAccent ? 'text-sky-500' : 'text-foreground';

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <MarketList
        countries={data.anchor_markets}
        emptyMessage="No anchor markets for selected filters."
        title="Anchor Markets"
        useAccent={useAccent}
      />
      <MarketList
        countries={data.peripheral_markets}
        emptyMessage="No peripheral markets for selected filters."
        title="Peripheral Markets"
        useAccent={useAccent}
      />
      <div className="rounded-md border bg-background p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">Country Dependency</h3>
            <InformationPopover ariaLabel="About country dependency" title="Country Dependency">
              Measures traffic concentration in the leading country and top three countries. Higher concentration means greater dependency on fewer markets.
            </InformationPopover>
          </div>
          <Badge variant={analysisVariant(data.dependency.dependency_level)}>
            {data.dependency.dependency_level}
          </Badge>
        </div>
        <div className="mt-4 grid gap-3 text-sm">
          <div className="flex justify-between gap-3">
            <span className="text-muted-foreground">Top 1 country share</span>
            <span className={`font-medium ${valueClass}`}>
              {percentFormatter.format(data.dependency.top1_country_share)}
            </span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-muted-foreground">Top 3 countries share</span>
            <span className={`font-medium ${valueClass}`}>
              {percentFormatter.format(data.dependency.top3_country_share)}
            </span>
          </div>
        </div>
      </div>
      <div className="rounded-md border bg-background p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">Presence Stability</h3>
            <InformationPopover ariaLabel="About presence stability" title="Presence Stability">
              Shows the share of days with positive traffic in the selected period: stable from 80%, irregular from 40%, and weak below 40%.
            </InformationPopover>
          </div>
          <Badge variant={analysisVariant(data.presence_stability.status)}>{data.presence_stability.status}</Badge>
        </div>
        <div className="mt-4 grid gap-3 text-sm">
          <div className="flex justify-between gap-3">
            <span className="text-muted-foreground">Active days</span>
            <span className={`font-medium ${valueClass}`}>
              {numberFormatter.format(data.presence_stability.active_days)}
            </span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-muted-foreground">Period days</span>
            <span className={`font-medium ${valueClass}`}>
              {numberFormatter.format(data.presence_stability.period_days)}
            </span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-muted-foreground">Stability rate</span>
            <span className={`font-medium ${valueClass}`}>
              {percentFormatter.format(data.presence_stability.stability_rate)}
            </span>
          </div>
        </div>
      </div>
      <div className="rounded-md border bg-background p-4 xl:col-span-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-foreground">Market Windows</h3>
          <InformationPopover ariaLabel="About market windows" title="Market Windows">
            Rule-based opportunities and risks detected from declining presence, small but rapidly growing markets, low stability, or high country dependency.
          </InformationPopover>
        </div>
        {data.market_windows.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No rule-based market signals for selected filters.</p>
        ) : (
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            {data.market_windows.map((window, index) => (
              <div
                className={`border-l-2 pl-3 ${useAccent ? 'border-sky-500' : 'border-primary'}`}
                key={`${window.country}-${window.signal}-${index}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`text-sm font-medium ${valueClass}`}>{window.country}</span>
                  <Badge variant="outline">{window.signal}</Badge>
                </div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{window.message}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
