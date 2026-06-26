import { InformationPopover } from '@/components/dashboard/information-popover';
import { SortableTableHeader } from '@/components/dashboard/sortable-table-header';
import { Badge } from '@/components/ui/badge';
import { useTableSort, type SortColumn } from '@/lib/dashboard/table-sorting';
import type { DerivedSignal, DerivedSignalSeverity } from '@/lib/types/analytics';
import type { ReactNode } from 'react';


const numberFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

function severity_variant(
  severity: DerivedSignalSeverity,
): 'destructive' | 'warning' | 'secondary' | 'outline' {
  if (severity === 'critical') {
    return 'destructive';
  }
  if (severity === 'high' || severity === 'medium') {
    return 'warning';
  }
  return 'secondary';
}

function format_metric(signal: DerivedSignal): string {
  if (signal.delta_percent !== null) {
    return percentFormatter.format(signal.delta_percent);
  }
  if (signal.delta_value !== null) {
    return numberFormatter.format(signal.delta_value);
  }
  if (signal.value !== null) {
    return numberFormatter.format(signal.value);
  }
  return 'None';
}

const headerDescriptions: Record<string, ReactNode> = {
  Severity: (
    <>
      <p><strong>low:</strong> informative or early-stage condition.</p>
      <p><strong>medium:</strong> material condition worth monitoring.</p>
      <p><strong>high:</strong> strong deviation or elevated analytical risk.</p>
      <p><strong>critical:</strong> highest-priority rule result.</p>
    </>
  ),
  Group: (
    <>
      <p><strong>growth:</strong> traffic movement.</p>
      <p><strong>volatility:</strong> stability or unusual variability.</p>
      <p><strong>competition:</strong> market structure.</p>
      <p><strong>territory:</strong> market presence.</p>
      <p><strong>channel:</strong> acquisition shifts.</p>
      <p><strong>quality:</strong> engagement quality.</p>
      <p><strong>device:</strong> desktop and mobile differences.</p>
    </>
  ),
  Type: (
    <>
      <p>Specific triggered rule.</p>
      <p><strong>new_activity:</strong> traffic appears after being absent.</p>
      <p><strong>growth_acceleration:</strong> traffic growth reaches the rule threshold.</p>
      <p><strong>traffic_decline:</strong> traffic falls enough to trigger a decline rule.</p>
      <p><strong>high_volatility:</strong> daily traffic varies strongly.</p>
      <p><strong>stable_market:</strong> daily traffic is comparatively stable.</p>
      <p><strong>high_concentration:</strong> leading companies hold a large traffic share.</p>
      <p><strong>low_competitive_noise:</strong> few active competitors are present.</p>
      <p><strong>fragmented_market:</strong> traffic is spread across many competitors.</p>
      <p><strong>overheated_market:</strong> growth appears together with high concentration.</p>
      <p><strong>low_noise_market:</strong> positive movement with limited competitor activity.</p>
      <p><strong>new_territory:</strong> meaningful traffic appears in a country.</p>
      <p><strong>forgotten_territory:</strong> country traffic falls close to inactivity.</p>
      <p><strong>channel_shift:</strong> channel share changes materially.</p>
      <p><strong>competitor_expansion:</strong> company expands into multiple active territories.</p>
      <p><strong>traffic_quality_degradation:</strong> engagement quality weakens.</p>
    </>
  ),
  Entity: 'Country, company, domain, channel, device, or selected analytical scope associated with the signal.',
  Period: 'Start and end dates used to calculate the signal and its comparison baseline.',
  'Value / Delta': 'Primary signal measurement. Delta percent is preferred, followed by absolute delta and current value.',
  Message: 'Human-readable explanation of the detected analytical condition.',
};

type SignalSortKey = 'entity' | 'group' | 'message' | 'period' | 'severity' | 'type' | 'value';

function SignalHeader({
  activeKey,
  align = 'left',
  label,
  onSort,
  sortDirection,
  sortKey,
}: {
  activeKey: SignalSortKey;
  align?: 'left' | 'right';
  label: string;
  onSort: (key: SignalSortKey) => void;
  sortDirection: 'asc' | 'desc';
  sortKey: SignalSortKey;
}) {
  return (
    <SortableTableHeader
      activeKey={activeKey}
      align={align}
      label={label}
      onSort={onSort}
      sortDirection={sortDirection}
      sortKey={sortKey}
    >
      <InformationPopover ariaLabel={`About ${label.toLowerCase()}`} title={label}>
        {headerDescriptions[label]}
      </InformationPopover>
    </SortableTableHeader>
  );
}

export function DerivedSignalTable({ signals, combinedScopes }: { signals: DerivedSignal[]; combinedScopes: boolean }) {
  const columns: SortColumn<DerivedSignal, SignalSortKey>[] = [
    { key: 'severity', getValue: (signal) => signal.severity },
    { key: 'group', getValue: (signal) => signal.signal_group },
    { key: 'type', getValue: (signal) => signal.signal_type },
    { key: 'entity', getValue: (signal) => `${signal.entity_type} ${signal.entity_id ?? ''}` },
    { key: 'period', getValue: (signal) => signal.date_from },
    { key: 'value', getValue: (signal) => signal.delta_percent ?? signal.delta_value ?? signal.value ?? 0 },
    { key: 'message', getValue: (signal) => signal.message },
  ];
  const { requestSort, sortedRows, sortState } = useTableSort(signals, columns, {
    direction: 'desc',
    key: 'severity',
  });

  return (
    <div className="overflow-hidden rounded-md border bg-background">
      <table className="w-full table-fixed text-xs">
        <thead className="bg-secondary text-muted-foreground">
          <tr>
            <SignalHeader activeKey={sortState.key} label="Severity" onSort={requestSort} sortDirection={sortState.direction} sortKey="severity" />
            <SignalHeader activeKey={sortState.key} label="Group" onSort={requestSort} sortDirection={sortState.direction} sortKey="group" />
            <SignalHeader activeKey={sortState.key} label="Type" onSort={requestSort} sortDirection={sortState.direction} sortKey="type" />
            <SignalHeader activeKey={sortState.key} label="Entity" onSort={requestSort} sortDirection={sortState.direction} sortKey="entity" />
            <SignalHeader activeKey={sortState.key} label="Period" onSort={requestSort} sortDirection={sortState.direction} sortKey="period" />
            <SignalHeader activeKey={sortState.key} align="right" label="Value / Delta" onSort={requestSort} sortDirection={sortState.direction} sortKey="value" />
            <SignalHeader activeKey={sortState.key} label="Message" onSort={requestSort} sortDirection={sortState.direction} sortKey="message" />
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((signal) => {
            const valueClass = combinedScopes || signal.scope === 'overall'
              ? 'text-foreground'
              : signal.scope === 'company'
                ? 'text-emerald-500'
                : 'text-sky-500';
            return (
            <tr className={`border-t align-top ${valueClass}`} key={signal.id}>
              <td className="px-2 py-2">
                <Badge className="whitespace-normal break-words text-[11px]" variant={severity_variant(signal.severity)}>{signal.severity}</Badge>
              </td>
              <td className="break-words px-2 py-2">{format_label(signal.signal_group)}</td>
              <td className="break-words px-2 py-2 font-medium">{format_label(signal.signal_type)}</td>
              <td className="break-words px-2 py-2">
                <span>{format_label(signal.entity_type)}</span>
                {signal.entity_id ? <span className="ml-1 text-xs text-muted-foreground">{signal.entity_id}</span> : null}
              </td>
              <td className="break-words px-2 py-2 text-xs text-muted-foreground">
                {signal.date_from} - {signal.date_to}
              </td>
              <td className="px-2 py-2 text-right font-medium">{format_metric(signal)}</td>
              <td className="break-words px-2 py-2 text-xs leading-5 text-muted-foreground">{signal.message}</td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
