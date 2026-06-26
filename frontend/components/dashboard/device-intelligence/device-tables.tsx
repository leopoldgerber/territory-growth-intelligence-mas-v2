import { InformationPopover } from '@/components/dashboard/information-popover';
import { SortableTableHeader } from '@/components/dashboard/sortable-table-header';
import { Badge } from '@/components/ui/badge';
import { useTableSort, type SortColumn } from '@/lib/dashboard/table-sorting';
import type { CompetitorDeviceQuality, DeviceTrendPoint } from '@/lib/types/analytics';

import { DeviceComparisonValue, type DeviceComparisonProps } from './device-comparison';


const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});
const numberFormatter = new Intl.NumberFormat('en-US');

function format_duration(seconds: number): string {
  const absoluteSeconds = Math.round(Math.abs(seconds));
  const minutes = Math.floor(absoluteSeconds / 60);
  const remainingSeconds = absoluteSeconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

export function DeviceTrendTable({ combinedScopes, companyScope, competitorScope }: DeviceComparisonProps) {
  const companyRows = new Map((companyScope?.device_trend ?? []).map((row) => [row.date, row]));
  const competitorRows = new Map((competitorScope?.device_trend ?? []).map((row) => [row.date, row]));
  const dates = Array.from(new Set([...companyRows.keys(), ...competitorRows.keys()])).sort();
  type TrendRow = {
    companyRow: DeviceTrendPoint | undefined;
    competitorRow: DeviceTrendPoint | undefined;
    date: string;
  };
  type TrendSortKey = 'date' | 'desktop_share' | 'desktop_visits' | 'mobile_share' | 'mobile_visits';
  const rows = dates.map((date) => ({
    companyRow: companyRows.get(date),
    competitorRow: competitorRows.get(date),
    date,
  }));

  function read_value(row: DeviceTrendPoint | undefined, field: keyof DeviceTrendPoint): string | null {
    if (!row) {
      return '0';
    }
    const value = row[field];
    return field.endsWith('_share') ? percentFormatter.format(value as number) : numberFormatter.format(value as number);
  }

  function read_sort_value(row: TrendRow, field: keyof DeviceTrendPoint): number | string {
    if (field === 'date') {
      return row.date;
    }
    return Number(row.companyRow?.[field] ?? 0) + Number(row.competitorRow?.[field] ?? 0);
  }

  const columns: SortColumn<TrendRow, TrendSortKey>[] = [
    { key: 'date', getValue: (row) => row.date },
    { key: 'desktop_visits', getValue: (row) => read_sort_value(row, 'desktop_visits') },
    { key: 'mobile_visits', getValue: (row) => read_sort_value(row, 'mobile_visits') },
    { key: 'desktop_share', getValue: (row) => read_sort_value(row, 'desktop_share') },
    { key: 'mobile_share', getValue: (row) => read_sort_value(row, 'mobile_share') },
  ];
  const { requestSort, sortedRows, sortState } = useTableSort(rows, columns, {
    direction: 'asc',
    key: 'date',
  });

  if (dates.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Daily Device Trend</h3>
      <div className="max-h-96 overflow-auto rounded-md border bg-background">
        <table className="w-full table-fixed text-sm">
          <thead className="sticky top-0 bg-secondary text-muted-foreground">
            <tr>
              <SortableTableHeader activeKey={sortState.key} label="Date" onSort={requestSort} sortDirection={sortState.direction} sortKey="date" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Desktop Visits" onSort={requestSort} sortDirection={sortState.direction} sortKey="desktop_visits" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Mobile Visits" onSort={requestSort} sortDirection={sortState.direction} sortKey="mobile_visits" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Desktop Share" onSort={requestSort} sortDirection={sortState.direction} sortKey="desktop_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Mobile Share" onSort={requestSort} sortDirection={sortState.direction} sortKey="mobile_share" />
            </tr>
          </thead>
          <tbody>
            {sortedRows.map(({ companyRow, competitorRow, date }) => {
              return (
                <tr className="border-t" key={date}>
                  <td className="px-3 py-2 font-medium text-foreground">{date}</td>
                  {(['desktop_visits', 'mobile_visits', 'desktop_share', 'mobile_share'] as const).map((field) => (
                    <td className="px-3 py-2 text-right" key={field}>
                      <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={read_value(companyRow, field)} competitorValue={competitorScope ? read_value(competitorRow, field) : null} />
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function CompetitorDeviceTable({ combinedScopes, companyScope, competitorScope }: DeviceComparisonProps) {
  const rows: Array<{ row: CompetitorDeviceQuality; tone: 'neutral' | 'company' | 'competitor' }> = [
    ...(companyScope?.competitor_device_quality ?? []).map((row) => ({ row, tone: combinedScopes ? 'neutral' as const : 'company' as const })),
    ...(competitorScope?.competitor_device_quality ?? []).map((row) => ({ row, tone: 'competitor' as const })),
  ];
  type DeviceQualitySortKey =
    | 'company'
    | 'desktop_bounce_rate'
    | 'desktop_duration'
    | 'desktop_share'
    | 'mobile_bounce_rate'
    | 'mobile_duration'
    | 'mobile_share'
    | 'quality_gap'
    | 'signal';
  const columns: SortColumn<{ row: CompetitorDeviceQuality; tone: 'neutral' | 'company' | 'competitor' }, DeviceQualitySortKey>[] = [
    { key: 'company', getValue: ({ row }) => row.company },
    { key: 'desktop_share', getValue: ({ row }) => row.desktop_share },
    { key: 'mobile_share', getValue: ({ row }) => row.mobile_share },
    { key: 'desktop_bounce_rate', getValue: ({ row }) => row.desktop_bounce_rate },
    { key: 'mobile_bounce_rate', getValue: ({ row }) => row.mobile_bounce_rate },
    { key: 'desktop_duration', getValue: ({ row }) => row.desktop_duration },
    { key: 'mobile_duration', getValue: ({ row }) => row.mobile_duration },
    { key: 'quality_gap', getValue: ({ row }) => row.quality_gap },
    { key: 'signal', getValue: ({ row }) => row.signal },
  ];
  const { requestSort, sortedRows, sortState } = useTableSort(rows, columns, {
    direction: 'asc',
    key: 'company',
  });

  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Company Device Quality</h3>
      <div className="overflow-hidden rounded-md border bg-background">
        <table className="w-full table-fixed text-xs">
          <thead className="bg-secondary text-muted-foreground">
            <tr>
              <SortableTableHeader activeKey={sortState.key} label="Company" onSort={requestSort} sortDirection={sortState.direction} sortKey="company" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Desktop Share" onSort={requestSort} sortDirection={sortState.direction} sortKey="desktop_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Mobile Share" onSort={requestSort} sortDirection={sortState.direction} sortKey="mobile_share" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Desktop Bounce" onSort={requestSort} sortDirection={sortState.direction} sortKey="desktop_bounce_rate" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Mobile Bounce" onSort={requestSort} sortDirection={sortState.direction} sortKey="mobile_bounce_rate" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Desktop Duration" onSort={requestSort} sortDirection={sortState.direction} sortKey="desktop_duration" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Mobile Duration" onSort={requestSort} sortDirection={sortState.direction} sortKey="mobile_duration" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Quality Gap" onSort={requestSort} sortDirection={sortState.direction} sortKey="quality_gap" />
              <SortableTableHeader activeKey={sortState.key} align="right" label="Signal" onSort={requestSort} sortDirection={sortState.direction} sortKey="signal">
                  <InformationPopover ariaLabel="About device quality signals" title="Signal">
                    <p><strong>mobile_quality_gap:</strong> mobile share is meaningful while desktop quality leads.</p>
                    <p><strong>desktop_quality_advantage:</strong> desktop quality leads by at least 15%.</p>
                    <p><strong>mobile_strength:</strong> mobile leads traffic with equal or stronger quality.</p>
                    <p><strong>balanced_device_quality:</strong> quality gap is below 10%.</p>
                    <p><strong>mixed_device_quality:</strong> none of the stronger classifications applies.</p>
                  </InformationPopover>
              </SortableTableHeader>
            </tr>
          </thead>
          <tbody>
            {sortedRows.map(({ row, tone }, index) => {
              const valueClass = tone === 'company' ? 'text-emerald-500' : tone === 'competitor' ? 'text-sky-500' : 'text-foreground';
              return (
                <tr className={`border-t ${valueClass}`} key={`${tone}-${row.company_id}-${index}`}>
                  <td className="break-words px-2 py-2 font-medium">{row.company}</td>
                  <td className="px-2 py-2 text-right">{percentFormatter.format(row.desktop_share)}</td>
                  <td className="px-2 py-2 text-right">{percentFormatter.format(row.mobile_share)}</td>
                  <td className="px-2 py-2 text-right">{percentFormatter.format(row.desktop_bounce_rate)}</td>
                  <td className="px-2 py-2 text-right">{percentFormatter.format(row.mobile_bounce_rate)}</td>
                  <td className="px-2 py-2 text-right">{format_duration(row.desktop_duration)}</td>
                  <td className="px-2 py-2 text-right">{format_duration(row.mobile_duration)}</td>
                  <td className="px-2 py-2 text-right">{percentFormatter.format(row.quality_gap)}</td>
                  <td className="px-2 py-2 text-right"><Badge className="ml-auto w-fit whitespace-normal break-words text-[11px]" variant="outline">{format_label(row.signal)}</Badge></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
