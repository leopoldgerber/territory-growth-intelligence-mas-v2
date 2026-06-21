import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';
import type { DerivedSignal, DerivedSignalSeverity } from '@/lib/types/analytics';


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

const headerDescriptions: Record<string, string> = {
  Severity: 'Low is informative, medium is material, high is a strong deviation, and critical is the highest-priority rule result.',
  Group: 'Growth covers traffic movement; volatility covers stability; competition covers market structure; territory covers market presence; channel covers acquisition shifts; quality covers engagement; device covers desktop and mobile differences.',
  Type: 'Specific triggered rule, including growth acceleration, traffic decline, new activity, volatility, concentration, expansion, channel shift, quality degradation, or device-quality conditions.',
  Entity: 'Country, company, domain, channel, device, or selected analytical scope associated with the signal.',
  Period: 'Start and end dates used to calculate the signal and its comparison baseline.',
  'Value / Delta': 'Primary signal measurement. Delta percent is preferred, followed by absolute delta and current value.',
  Message: 'Human-readable explanation of the detected analytical condition.',
};

function SignalHeader({ label, align = 'left' }: { label: string; align?: 'left' | 'right' }) {
  return (
    <th className={`px-3 py-2 font-medium ${align === 'right' ? 'text-right' : 'text-left'}`}>
      <span className={`flex items-center gap-1 ${align === 'right' ? 'justify-end' : 'justify-start'}`}>
        <span>{label}</span>
        <InformationPopover ariaLabel={`About ${label.toLowerCase()}`} title={label}>
          {headerDescriptions[label]}
        </InformationPopover>
      </span>
    </th>
  );
}

export function DerivedSignalTable({ signals, combinedScopes }: { signals: DerivedSignal[]; combinedScopes: boolean }) {
  return (
    <div className="overflow-x-auto rounded-md border bg-background">
      <table className="w-full min-w-[1040px] text-sm">
        <thead className="bg-secondary text-muted-foreground">
          <tr>
            <SignalHeader label="Severity" />
            <SignalHeader label="Group" />
            <SignalHeader label="Type" />
            <SignalHeader label="Entity" />
            <SignalHeader label="Period" />
            <SignalHeader align="right" label="Value / Delta" />
            <SignalHeader label="Message" />
          </tr>
        </thead>
        <tbody>
          {signals.map((signal) => {
            const valueClass = combinedScopes || signal.scope === 'overall'
              ? 'text-foreground'
              : signal.scope === 'company'
                ? 'text-emerald-500'
                : 'text-sky-500';
            return (
            <tr className={`border-t align-top ${valueClass}`} key={signal.id}>
              <td className="px-3 py-2">
                <Badge variant={severity_variant(signal.severity)}>{signal.severity}</Badge>
              </td>
              <td className="px-3 py-2">{format_label(signal.signal_group)}</td>
              <td className="px-3 py-2 font-medium">{format_label(signal.signal_type)}</td>
              <td className="px-3 py-2">
                <span>{format_label(signal.entity_type)}</span>
                {signal.entity_id ? <span className="ml-1 text-xs text-muted-foreground">{signal.entity_id}</span> : null}
              </td>
              <td className="whitespace-nowrap px-3 py-2 text-xs text-muted-foreground">
                {signal.date_from} - {signal.date_to}
              </td>
              <td className="px-3 py-2 text-right font-medium">{format_metric(signal)}</td>
              <td className="max-w-md px-3 py-2 text-xs leading-5 text-muted-foreground">{signal.message}</td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
