import { InformationPopover } from '@/components/dashboard/information-popover';
import { SortableTableHeader } from '@/components/dashboard/sortable-table-header';
import { Badge } from '@/components/ui/badge';
import { useTableSort, type SortColumn } from '@/lib/dashboard/table-sorting';
import type { CompetitorChannelDependency, TopSourceItem } from '@/lib/types/analytics';

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
  type DependencySortKey =
    | 'company'
    | 'dependency_level'
    | 'direct_share'
    | 'dominant_channel'
    | 'dominant_channel_share'
    | 'paid_share'
    | 'referral_share'
    | 'search_share'
    | 'social_share'
    | 'total_traffic';
  const columns: SortColumn<ScopedRow<CompetitorChannelDependency>, DependencySortKey>[] = [
    { key: 'company', getValue: ({ row }) => row.company },
    { key: 'total_traffic', getValue: ({ row }) => row.total_traffic },
    { key: 'dominant_channel', getValue: ({ row }) => row.dominant_channel },
    { key: 'dominant_channel_share', getValue: ({ row }) => row.dominant_channel_share },
    { key: 'direct_share', getValue: ({ row }) => row.direct_share },
    { key: 'search_share', getValue: ({ row }) => row.search_share },
    { key: 'paid_share', getValue: ({ row }) => row.paid_share },
    { key: 'referral_share', getValue: ({ row }) => row.referral_share },
    { key: 'social_share', getValue: ({ row }) => row.social_share },
    { key: 'dependency_level', getValue: ({ row }) => row.dependency_level },
  ];
  const { requestSort, sortedRows, sortState } = useTableSort(rows, columns, {
    direction: 'desc',
    key: 'total_traffic',
  });

  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-foreground">Company Channel Dependency</h3>
        <InformationPopover ariaLabel="About company channel dependency" title="Company Channel Dependency">
          <p>Channel shares calculated for each company.</p>
          <p><strong>low:</strong> dominant channel share is below 40%.</p>
          <p><strong>medium:</strong> dominant channel share is from 40% to 59.9%.</p>
          <p><strong>high:</strong> dominant channel share is at least 60%.</p>
        </InformationPopover>
      </div>
      <div className="overflow-hidden rounded-md border bg-background">
        <table className="w-full table-fixed text-xs">
          <thead className="bg-secondary text-muted-foreground">
            <tr>
              <SortableTableHeader activeKey={sortState.key} label="Company" onSort={requestSort} sortDirection={sortState.direction} sortKey="company" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Total Traffic" onSort={requestSort} sortDirection={sortState.direction} sortKey="total_traffic" />
              <SortableTableHeader activeKey={sortState.key} label="Dominant Channel" onSort={requestSort} sortDirection={sortState.direction} sortKey="dominant_channel" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Dominant Share" onSort={requestSort} sortDirection={sortState.direction} sortKey="dominant_channel_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Direct" onSort={requestSort} sortDirection={sortState.direction} sortKey="direct_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Search" onSort={requestSort} sortDirection={sortState.direction} sortKey="search_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Paid" onSort={requestSort} sortDirection={sortState.direction} sortKey="paid_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Referral" onSort={requestSort} sortDirection={sortState.direction} sortKey="referral_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Social" onSort={requestSort} sortDirection={sortState.direction} sortKey="social_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Dependency" onSort={requestSort} sortDirection={sortState.direction} sortKey="dependency_level">
                  <InformationPopover ariaLabel="About dependency levels" title="Dependency">
                    <p><strong>low:</strong> dominant channel share is below 40%.</p>
                    <p><strong>medium:</strong> dominant channel share is from 40% to 59.9%.</p>
                    <p><strong>high:</strong> dominant channel share is at least 60%.</p>
                  </InformationPopover>
              </SortableTableHeader>
            </tr>
          </thead>
          <tbody>
            {sortedRows.map(({ row, tone }, index) => (
              <tr className="border-t" key={`${tone}-${row.company_id}-${index}`}>
                <td className={`break-words px-2 py-2 font-medium ${channelValueClasses[tone]}`}>{row.company}</td>
                <td className={`px-2 py-2 text-right ${channelValueClasses[tone]}`}>
                  {numberFormatter.format(row.total_traffic)}
                </td>
                <td className={`break-words px-2 py-2 ${channelValueClasses[tone]}`}>{format_label(row.dominant_channel)}</td>
                <td className={`px-2 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.dominant_channel_share)}</td>
                <td className={`px-2 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.direct_share)}</td>
                <td className={`px-2 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.search_share)}</td>
                <td className={`px-2 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.paid_share)}</td>
                <td className={`px-2 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.referral_share)}</td>
                <td className={`px-2 py-2 text-right ${channelValueClasses[tone]}`}>{percentFormatter.format(row.social_share)}</td>
                <td className="px-2 py-2 text-right">
                  <Badge className="ml-auto w-fit whitespace-normal break-words text-[11px]" variant={dependency_variant(row.dependency_level)}>
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
  type SourceSortKey = 'search_source' | 'share' | 'source_type' | 'traffic' | 'traffic_type';
  const columns: SortColumn<ScopedRow<TopSourceItem>, SourceSortKey>[] = [
    { key: 'source_type', getValue: ({ row }) => row.source_type },
    { key: 'traffic_type', getValue: ({ row }) => row.traffic_type },
    { key: 'search_source', getValue: ({ row }) => row.search_source },
    { key: 'traffic', getValue: ({ row }) => row.traffic },
    { key: 'share', getValue: ({ row }) => row.share },
  ];
  const { requestSort, sortedRows, sortState } = useTableSort(rows, columns, {
    direction: 'desc',
    key: 'traffic',
  });

  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-foreground">Top Journey Sources</h3>
        <InformationPopover ariaLabel="About top journey sources" title="Top Journey Sources">
          <p>Highest-traffic combinations of source type, traffic type, and named source within the selected scopes.</p>
          <p><strong>paid:</strong> source traffic classified as paid acquisition.</p>
          <p><strong>organic:</strong> source traffic classified as non-paid acquisition.</p>
          <p><strong>unknown:</strong> source traffic without paid or organic classification.</p>
        </InformationPopover>
      </div>
      <div className="overflow-hidden rounded-md border bg-background">
        <table className="w-full table-fixed text-sm">
          <thead className="bg-secondary text-muted-foreground">
            <tr>
              <SortableTableHeader activeKey={sortState.key} label="Source Type" onSort={requestSort} sortDirection={sortState.direction} sortKey="source_type" />
              <SortableTableHeader activeKey={sortState.key} label="Traffic Type" onSort={requestSort} sortDirection={sortState.direction} sortKey="traffic_type" />
              <SortableTableHeader activeKey={sortState.key} label="Source" onSort={requestSort} sortDirection={sortState.direction} sortKey="search_source" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Traffic" onSort={requestSort} sortDirection={sortState.direction} sortKey="traffic" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Share" onSort={requestSort} sortDirection={sortState.direction} sortKey="share" />
            </tr>
          </thead>
          <tbody>
            {sortedRows.map(({ row, tone }, index) => (
              <tr className="border-t" key={`${tone}-${row.source_type}-${row.traffic_type}-${row.search_source}-${index}`}>
                <td className={`break-words px-3 py-2 font-medium ${channelValueClasses[tone]}`}>
                  {format_label(row.source_type)}
                </td>
                <td className={`break-words px-3 py-2 ${channelValueClasses[tone]}`}>{format_label(row.traffic_type)}</td>
                <td className={`break-words px-3 py-2 ${channelValueClasses[tone]}`}>{row.search_source}</td>
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
