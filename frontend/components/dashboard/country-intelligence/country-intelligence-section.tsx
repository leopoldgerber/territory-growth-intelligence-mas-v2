'use client';

import type { ReactNode } from 'react';

import { InformationPopover } from '@/components/dashboard/information-popover';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useCountryIntelligenceQuery } from '@/lib/api/analytics-queries';
import type { CountryIntelligenceResponse, TrafficTrendPoint } from '@/lib/types/analytics';

const numberFormatter = new Intl.NumberFormat('en-US');
const compactFormatter = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
});
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

const marketSignalTypes = [
  {
    status: 'no_data',
    description: 'No traffic is available for the selected filters and period.',
  },
  {
    status: 'insufficient_data',
    description: 'Fewer than two dated traffic points are available for comparison.',
  },
  {
    status: 'new_activity',
    description: 'Traffic is absent in the first half of the period and appears in the second half.',
  },
  {
    status: 'falling',
    description: 'Traffic in the second half of the period decreased by at least 10%.',
  },
  {
    status: 'stable',
    description: 'Traffic change between the two halves remains between -5% and 5%.',
  },
  {
    status: 'promising',
    description: 'Traffic grew by at least 10%, leader share is below 40%, and bounce rate is below 55%.',
  },
  {
    status: 'overheated',
    description: 'Traffic grew by at least 10%, while the leading company holds at least 50% of traffic.',
  },
  {
    status: 'growing',
    description: 'Traffic grew by at least 10% without meeting the promising or overheated conditions.',
  },
  {
    status: 'mixed',
    description: 'Traffic movement does not match any of the other signal conditions.',
  },
];

function formatNumber(value: number): string {
  return numberFormatter.format(Math.round(value));
}

function formatCompact(value: number): string {
  return compactFormatter.format(Math.round(value));
}

function formatPercent(value: number): string {
  return percentFormatter.format(value);
}

function formatDuration(seconds: number): string {
  const totalSeconds = Math.round(seconds);
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

type ScopeVisibility = {
  combinedScopes: boolean;
  showCompany: boolean;
  showCompetitors: boolean;
};

type ComparisonValueProps = ScopeVisibility & {
  companyValue: ReactNode;
  competitorValue: ReactNode;
  size?: 'default' | 'large';
};

function ComparisonValue({
  companyValue,
  competitorValue,
  combinedScopes,
  showCompany,
  showCompetitors,
  size = 'default',
}: ComparisonValueProps) {
  if (!showCompany && !showCompetitors) {
    return null;
  }

  if (combinedScopes) {
    return (
      <div className={size === 'large' ? 'mt-2 text-xl font-semibold text-foreground' : 'font-medium text-foreground'}>
        {companyValue}
      </div>
    );
  }

  return (
    <div className={size === 'large' ? 'mt-2 flex items-baseline gap-2 text-xl font-semibold' : 'flex gap-2 font-medium'}>
      {showCompany ? <span className="text-emerald-500">{companyValue}</span> : null}
      {showCompany && showCompetitors ? <span className="text-muted-foreground">|</span> : null}
      {showCompetitors ? <span className="text-sky-500">{competitorValue}</span> : null}
    </div>
  );
}

function signalVariant(status: string): 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'destructive' {
  if (status === 'promising' || status === 'growing' || status === 'new_activity') {
    return 'success';
  }
  if (status === 'falling' || status === 'overheated') {
    return 'warning';
  }
  if (status === 'no_data') {
    return 'outline';
  }
  return 'secondary';
}

function trendSlice(trend: TrafficTrendPoint[]): TrafficTrendPoint[] {
  if (trend.length <= 14) {
    return trend;
  }
  return trend.slice(-14);
}

function LoadingState() {
  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-4">
        <Skeleton className="h-6 w-56" />
        <div className="grid gap-3 md:grid-cols-5">
          {Array.from({ length: 5 }).map((_, index) => (
            <Skeleton key={index} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    </section>
  );
}

function SummaryCards({
  data,
  combinedScopes,
  showCompany,
  showCompetitors,
}: { data: CountryIntelligenceResponse } & ScopeVisibility) {
  const selectedPeriod =
    data.filters.date_from && data.filters.date_to ? `${data.filters.date_from} - ${data.filters.date_to}` : 'All';
  const cards = [
    {
      label: 'Total Traffic',
      companyValue: formatNumber(data.summary.total_traffic),
      competitorValue: formatNumber(data.competitor_summary.total_traffic),
    },
    {
      label: 'Active Companies',
      companyValue: formatNumber(data.summary.active_competitors),
      competitorValue: formatNumber(data.competitor_summary.active_competitors),
    },
    {
      label: 'Active Domains',
      companyValue: formatNumber(data.summary.active_domains),
      competitorValue: formatNumber(data.competitor_summary.active_domains),
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => (
        <div key={card.label} className="rounded-md border bg-background p-4">
          <p className="text-xs font-medium text-muted-foreground">{card.label}</p>
          <ComparisonValue
            companyValue={card.companyValue}
            competitorValue={card.competitorValue}
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
            size="large"
          />
        </div>
      ))}
      <div className="rounded-md border bg-background p-4">
        <p className="text-xs font-medium text-muted-foreground">Selected Countries</p>
        <p className="mt-2 truncate text-xl font-semibold text-foreground">
          {formatNumber(data.selected_country_count)}
        </p>
      </div>
      <div className="rounded-md border bg-background p-4">
        <p className="text-xs font-medium text-muted-foreground">Selected Period</p>
        <p className="mt-2 truncate text-base font-semibold text-foreground">{selectedPeriod}</p>
      </div>
    </div>
  );
}

function TopCompetitorsTable({
  data,
  combinedScopes,
  showCompetitors,
}: {
  data: CountryIntelligenceResponse;
  combinedScopes: boolean;
  showCompetitors: boolean;
}) {
  if (!showCompetitors) {
    return <p className="text-sm text-muted-foreground">Competitors are not selected.</p>;
  }

  if (data.top_competitors.length === 0) {
    return (
      <Alert>
        <AlertTitle>No competitors</AlertTitle>
        <AlertDescription>No competitor traffic was found for selected filters.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border">
      <table className="w-full text-sm">
        <thead className="bg-secondary text-muted-foreground">
          <tr>
            <th className="px-3 py-2 text-left font-medium">Rank</th>
            <th className="px-3 py-2 text-left font-medium">Company</th>
            <th className="px-3 py-2 text-right font-medium">Traffic</th>
            <th className="px-3 py-2 text-right font-medium">Traffic Share</th>
            <th className="px-3 py-2 text-right font-medium">Domains Count</th>
          </tr>
        </thead>
        <tbody>
          {data.top_competitors.map((competitor, index) => (
            <tr key={competitor.company_id} className="border-t">
              <td className="px-3 py-2 text-muted-foreground">{index + 1}</td>
              <td className={`px-3 py-2 font-medium ${combinedScopes ? 'text-foreground' : 'text-sky-500'}`}>
                {competitor.company}
              </td>
              <td className={`px-3 py-2 text-right ${combinedScopes ? 'text-foreground' : 'text-sky-500'}`}>
                {formatNumber(competitor.traffic)}
              </td>
              <td className={`px-3 py-2 text-right ${combinedScopes ? 'text-foreground' : 'text-sky-500'}`}>
                {formatPercent(competitor.traffic_share)}
              </td>
              <td className={`px-3 py-2 text-right ${combinedScopes ? 'text-foreground' : 'text-sky-500'}`}>
                {formatNumber(competitor.domains_count)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TrafficTrend({
  data,
  combinedScopes,
  showCompany,
  showCompetitors,
}: { data: CountryIntelligenceResponse } & ScopeVisibility) {
  const companyTrend = new Map(data.traffic_trend.map((point) => [point.date, point.traffic]));
  const competitorTrend = new Map(data.competitor_traffic_trend.map((point) => [point.date, point.traffic]));
  const dates = Array.from(new Set([...companyTrend.keys(), ...competitorTrend.keys()])).sort();
  const points = trendSlice(
    dates.map((date) => ({
      date,
      traffic: Math.max(companyTrend.get(date) ?? 0, competitorTrend.get(date) ?? 0),
    })),
  );
  const maxTraffic = Math.max(...points.map((point) => point.traffic), 0);

  if (points.length === 0) {
    return <p className="text-sm text-muted-foreground">No daily trend points for selected filters.</p>;
  }

  return (
    <div className="grid gap-2">
      {points.map((point) => {
        const companyTraffic = companyTrend.get(point.date) ?? 0;
        const competitorTraffic = competitorTrend.get(point.date) ?? 0;
        const companyWidth = maxTraffic === 0 ? 0 : Math.max((companyTraffic / maxTraffic) * 100, 2);
        const competitorWidth = maxTraffic === 0 ? 0 : Math.max((competitorTraffic / maxTraffic) * 100, 2);

        return (
          <div key={point.date} className="grid gap-1">
            <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
              <span>{point.date}</span>
              <ComparisonValue
                companyValue={formatCompact(companyTraffic)}
                competitorValue={formatCompact(competitorTraffic)}
                combinedScopes={combinedScopes}
                showCompany={showCompany}
                showCompetitors={showCompetitors}
              />
            </div>
            {showCompany ? (
              <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
                <div
                  className={`h-full rounded-full ${combinedScopes ? 'bg-primary' : 'bg-emerald-500'}`}
                  style={{ width: `${companyWidth}%` }}
                />
              </div>
            ) : null}
            {showCompetitors && !combinedScopes ? (
              <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
                <div className="h-full rounded-full bg-sky-500" style={{ width: `${competitorWidth}%` }} />
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function SplitBar({
  label,
  companyValue,
  companyShare,
  competitorValue,
  competitorShare,
  combinedScopes,
  showCompany,
  showCompetitors,
}: {
  label: string;
  companyValue: number;
  companyShare: number;
  competitorValue: number;
  competitorShare: number;
} & ScopeVisibility) {
  return (
    <div className="grid gap-1.5">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="text-muted-foreground">{label}</span>
        <ComparisonValue
          companyValue={`${formatNumber(companyValue)} / ${formatPercent(companyShare)}`}
          competitorValue={`${formatNumber(competitorValue)} / ${formatPercent(competitorShare)}`}
          combinedScopes={combinedScopes}
          showCompany={showCompany}
          showCompetitors={showCompetitors}
        />
      </div>
      {showCompany ? (
        <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
          <div
            className={`h-full rounded-full ${combinedScopes ? 'bg-primary' : 'bg-emerald-500'}`}
            style={{ width: `${companyShare * 100}%` }}
          />
        </div>
      ) : null}
      {showCompetitors && !combinedScopes ? (
        <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
          <div className="h-full rounded-full bg-sky-500" style={{ width: `${competitorShare * 100}%` }} />
        </div>
      ) : null}
    </div>
  );
}

function ComparisonRow({
  label,
  companyValue,
  competitorValue,
  combinedScopes,
  showCompany,
  showCompetitors,
}: { label: string; companyValue: string; competitorValue: string } & ScopeVisibility) {
  return (
    <div className="flex justify-between gap-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <ComparisonValue
        companyValue={companyValue}
        competitorValue={competitorValue}
        combinedScopes={combinedScopes}
        showCompany={showCompany}
        showCompetitors={showCompetitors}
      />
    </div>
  );
}

function MetricPanels({
  data,
  combinedScopes,
  showCompany,
  showCompetitors,
}: { data: CountryIntelligenceResponse } & ScopeVisibility) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      <div className="rounded-md border bg-background p-4">
        <h3 className="text-sm font-semibold text-foreground">Desktop / Mobile Split</h3>
        <div className="mt-4 grid gap-4">
          <SplitBar
            companyShare={data.device_split.desktop_share}
            companyValue={data.device_split.desktop_traffic}
            competitorShare={data.competitor_device_split.desktop_share}
            competitorValue={data.competitor_device_split.desktop_traffic}
            label="Desktop"
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
          />
          <SplitBar
            companyShare={data.device_split.mobile_share}
            companyValue={data.device_split.mobile_traffic}
            competitorShare={data.competitor_device_split.mobile_share}
            competitorValue={data.competitor_device_split.mobile_traffic}
            label="Mobile"
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
          />
        </div>
      </div>
      <div className="rounded-md border bg-background p-4">
        <h3 className="text-sm font-semibold text-foreground">Bounce / No-Bounce</h3>
        <div className="mt-4 grid gap-3 text-sm">
          <ComparisonRow
            companyValue={formatNumber(data.bounce.no_bounce)}
            competitorValue={formatNumber(data.competitor_bounce.no_bounce)}
            label="No-bounce"
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
          />
          <ComparisonRow
            companyValue={formatNumber(data.bounce.bounce)}
            competitorValue={formatNumber(data.competitor_bounce.bounce)}
            label="Bounce"
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
          />
          <ComparisonRow
            companyValue={formatPercent(data.bounce.bounce_rate)}
            competitorValue={formatPercent(data.competitor_bounce.bounce_rate)}
            label="Bounce rate"
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
          />
        </div>
      </div>
      <div className="rounded-md border bg-background p-4">
        <h3 className="text-sm font-semibold text-foreground">Engagement</h3>
        <div className="mt-4 grid gap-3 text-sm">
          <ComparisonRow
            companyValue={formatNumber(data.engagement.unique_visitors)}
            competitorValue={formatNumber(data.competitor_engagement.unique_visitors)}
            label="Unique visitors"
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
          />
          <ComparisonRow
            companyValue={data.engagement.pages_per_visit.toFixed(2)}
            competitorValue={data.competitor_engagement.pages_per_visit.toFixed(2)}
            label="Pages per visit"
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
          />
          <ComparisonRow
            companyValue={formatDuration(data.engagement.avg_visit_duration)}
            competitorValue={formatDuration(data.competitor_engagement.avg_visit_duration)}
            label="Avg visit duration"
            combinedScopes={combinedScopes}
            showCompany={showCompany}
            showCompetitors={showCompetitors}
          />
        </div>
      </div>
    </div>
  );
}

function MarketSignalHeader() {
  return (
    <div className="flex items-center justify-between gap-3">
      <h3 className="text-sm font-semibold text-foreground">Market Signal</h3>
      <InformationPopover
        ariaLabel="About market signal types"
        className="max-h-96 w-[min(32rem,calc(100vw-3rem))] overflow-y-auto"
        title="Market signal types"
      >
        <p>The selected period is split into two halves. Traffic in the second half is compared with the first.</p>
        <div className="mt-3 grid gap-3">
          {marketSignalTypes.map((signal) => (
            <div className="grid gap-1" key={signal.status}>
              <Badge className="w-fit" variant={signalVariant(signal.status)}>
                {signal.status}
              </Badge>
              <p>{signal.description}</p>
            </div>
          ))}
        </div>
      </InformationPopover>
    </div>
  );
}

function MarketSignal({
  data,
  combinedScopes,
  showCompany,
  showCompetitors,
}: { data: CountryIntelligenceResponse } & ScopeVisibility) {
  if (combinedScopes) {
    return (
      <div className="rounded-md border bg-background p-4">
        <MarketSignalHeader />
        <div className="mt-3 border-l-2 border-primary pl-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-foreground">All Companies</span>
            <Badge variant={signalVariant(data.market_signal.status)}>{data.market_signal.status}</Badge>
            <Badge variant="outline">{formatPercent(data.market_signal.growth_rate)}</Badge>
          </div>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{data.market_signal.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border bg-background p-4">
      <MarketSignalHeader />
      <div className="mt-3 grid gap-4 md:grid-cols-2">
        {showCompany ? (
          <div className="border-l-2 border-emerald-500 pl-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-emerald-500">Company</span>
              <Badge variant={signalVariant(data.market_signal.status)}>{data.market_signal.status}</Badge>
              <Badge variant="outline">{formatPercent(data.market_signal.growth_rate)}</Badge>
            </div>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{data.market_signal.message}</p>
          </div>
        ) : null}
        {showCompetitors ? (
          <div className="border-l-2 border-sky-500 pl-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-sky-500">Competitors</span>
              <Badge variant={signalVariant(data.competitor_market_signal.status)}>
                {data.competitor_market_signal.status}
              </Badge>
              <Badge variant="outline">{formatPercent(data.competitor_market_signal.growth_rate)}</Badge>
            </div>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {data.competitor_market_signal.message}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function CountryIntelligenceSection() {
  const countryIntelligenceQuery = useCountryIntelligenceQuery();

  if (countryIntelligenceQuery.isLoading) {
    return <LoadingState />;
  }

  if (countryIntelligenceQuery.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Failed to load country intelligence.</AlertTitle>
        <AlertDescription>Check that the backend is running and the analytics endpoint is available.</AlertDescription>
      </Alert>
    );
  }

  const data = countryIntelligenceQuery.data;

  if (!data) {
    return (
      <section className="rounded-md border bg-card/40 p-5">
        <div className="space-y-4">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold tracking-normal text-foreground">Market Overview</h2>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Country-level traffic and market analysis for selected dashboard filters.
            </p>
          </div>
          <Alert>
            <AlertTitle>No country data found for selected filters.</AlertTitle>
            <AlertDescription>Try changing the period, country, or domain filter.</AlertDescription>
          </Alert>
        </div>
      </section>
    );
  }

  const showCompany = data.filters.company !== 'none';
  const showCompetitors = data.filters.competitors !== 'none';
  const combinedScopes =
    data.filters.company === 'all' &&
    data.filters.competitors === 'all' &&
    data.filters.company_domain === data.filters.competitor_domain;

  if (!showCompany && !showCompetitors) {
    return (
      <section className="rounded-md border bg-card/40 p-5">
        <div className="space-y-4">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold tracking-normal text-foreground">Market Overview</h2>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Country-level traffic and market analysis for selected dashboard filters.
            </p>
          </div>
          <Alert>
            <AlertTitle>Company and competitors are not selected.</AlertTitle>
            <AlertDescription>Select a company or competitors to display market indicators.</AlertDescription>
          </Alert>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-md border bg-card/40 p-5">
      <div className="space-y-5">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold tracking-normal text-foreground">Market Overview</h2>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Country-level traffic and market analysis for selected dashboard filters.
          </p>
        </div>
        <SummaryCards
          data={data}
          combinedScopes={combinedScopes}
          showCompany={showCompany}
          showCompetitors={showCompetitors}
        />
        <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground">Top Competitors</h3>
            <TopCompetitorsTable
              data={data}
              combinedScopes={combinedScopes}
              showCompetitors={showCompetitors}
            />
          </div>
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground">Traffic Trend</h3>
            <TrafficTrend
              data={data}
              combinedScopes={combinedScopes}
              showCompany={showCompany}
              showCompetitors={showCompetitors}
            />
          </div>
        </div>
        <MetricPanels
          data={data}
          combinedScopes={combinedScopes}
          showCompany={showCompany}
          showCompetitors={showCompetitors}
        />
        <MarketSignal
          data={data}
          combinedScopes={combinedScopes}
          showCompany={showCompany}
          showCompetitors={showCompetitors}
        />
      </div>
    </section>
  );
}
