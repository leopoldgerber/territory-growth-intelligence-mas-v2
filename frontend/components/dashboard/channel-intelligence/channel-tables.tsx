import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';

import type { ChannelComparisonProps } from './channel-comparison';
import { channelValueClasses, type ChannelScopeTone } from './channel-scope-style';


const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

type ScopedRow<T> = {
  row: T;
  tone: ChannelScopeTone;
};

function format_label(value: string | null): string {
  if (!value) {
    return 'None';
  }
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

function dependency_variant(status: string): 'default' | 'secondary' | 'warning' {
  if (status === 'high') {
    return 'warning';
  }
  if (status === 'low') {
    return 'secondary';
  }
  return 'default';
}

function merge_rows<T>(
  combinedScopes: boolean,
  companyRows: T[],
  competitorRows: T[],
): ScopedRow<T>[] {
  return [
    ...companyRows.map((row) => ({ row, tone: combinedScopes ? 'neutral' as const : 'company' as const })),
    ...competitorRows.map((row) => ({ row, tone: 'competitor' as const })),
  ];
}

export function ChannelDependencyTable({
  combinedScopes,
  companyScope,
  competitorScope,
}: ChannelComparisonProps) {
  const rows = merge_rows(
    combinedScopes,
    companyScope?.company_channel_dependency ?? [],
    competitorScope?.company_channel_dependency ?? [],
  );

  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-foreground">Company Channel Dependency</h3>
        <InformationPopover ariaLabel="About company channel dependency" title="Company Channel Dependency">
          Channel shares calculated for each company. Dependency is high from 60% dominant share, medium from 40%, and low otherwise.
        </InformationPopover>
      </div>
      <div className="overflow-x-auto rounded-md border bg-background">
        <table className="w-full min-w-[980px] text-sm">
          <thead className="bg-secondary text-muted-foreground">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Company</th>
              <th className="px-3 py-2 text-right font-medium">Total Traffic</th>
              <th className="px-3 py-2 text-left font-medium">Dominant Channel</th>
              <th className="px-3 py-2 text-right font-medium">Dominant Share</th>
              <th className="px-3 py-2 text-right font-medium">Direct</th>
              <th className="px-3 py-2 text-right font-medium">Search</th>
              <th className="px-3 py-2 text-right font-medium">Paid</th>
              <th className="px-3 py-2 text-right font-medium">Referral</th>
              <th className="px-3 py-2 text-right font-medium">Social</th>
              <th className="px-3 py-2 text-right font-medium">Dependency</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ row, tone }, index) => (
              <tr className="border-t" key={`${tone}-${row.company_id}-${index}`}>
                <td className={`px-3 py-2 font-medium ${channelValueClasses[tone]}`}>{row.company}</td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>
                  {numberFormatter.format(row.total_traffic)}
                </td>
                <td className={`px-3 py-2 ${channelValueClasses[tone]}`}>{format_label(row.dominant_channel)}</td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.dominant_channel_share)}</td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.direct_share)}</td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.search_share)}</td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.paid_share)}</td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.referral_share)}</td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.social_share)}</td>
                <td className="px-3 py-2 text-right">
                  <Badge className="ml-auto w-fit" variant={dependency_variant(row.dependency_level)}>
                    {row.dependency_level}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function TopSourcesTable({ combinedScopes, companyScope, competitorScope }: ChannelComparisonProps) {
  const rows = merge_rows(
    combinedScopes,
    companyScope?.top_sources ?? [],
    competitorScope?.top_sources ?? [],
  );

  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-foreground">Top Journey Sources</h3>
        <InformationPopover ariaLabel="About top journey sources" title="Top Journey Sources">
          Highest-traffic combinations of source type, traffic type, and named source within the selected scopes.
        </InformationPopover>
      </div>
      <div className="overflow-x-auto rounded-md border bg-background">
        <table className="w-full min-w-[680px] text-sm">
          <thead className="bg-secondary text-muted-foreground">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Source Type</th>
              <th className="px-3 py-2 text-left font-medium">Traffic Type</th>
              <th className="px-3 py-2 text-left font-medium">Source</th>
              <th className="px-3 py-2 text-right font-medium">Traffic</th>
              <th className="px-3 py-2 text-right font-medium">Share</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ row, tone }, index) => (
              <tr className="border-t" key={`${tone}-${row.source_type}-${row.traffic_type}-${row.search_source}-${index}`}>
                <td className={`px-3 py-2 font-medium ${channelValueClasses[tone]}`}>
                  {format_label(row.source_type)}
                </td>
                <td className={`px-3 py-2 ${channelValueClasses[tone]}`}>{format_label(row.traffic_type)}</td>
                <td className={`px-3 py-2 ${channelValueClasses[tone]}`}>{row.search_source}</td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>
                  {numberFormatter.format(row.traffic)}
                </td>
                <td className={`px-3 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.share)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
