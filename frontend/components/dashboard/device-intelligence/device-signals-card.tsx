import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';
import type { DeviceSignal } from '@/lib/types/analytics';

import type { DeviceComparisonProps } from './device-comparison';


function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

function signal_variant(severity: string): 'secondary' | 'warning' {
  return severity === 'medium' ? 'warning' : 'secondary';
}

function SignalItems({ items, tone }: { items: DeviceSignal[]; tone: 'neutral' | 'company' | 'competitor' }) {
  const borderClass = tone === 'company' ? 'border-emerald-500' : tone === 'competitor' ? 'border-sky-500' : 'border-primary';
  const valueClass = tone === 'company' ? 'text-emerald-500' : tone === 'competitor' ? 'text-sky-500' : 'text-foreground';
  return items.map((item, index) => (
    <div className={`border-l-2 pl-3 ${borderClass}`} key={`${tone}-${item.type}-${index}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`text-sm font-medium ${valueClass}`}>{format_label(item.type)}</span>
        <Badge variant={signal_variant(item.severity)}>{item.severity}</Badge>
      </div>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.message}</p>
    </div>
  ));
}

export function DeviceSignalsCard({ combinedScopes, companyScope, competitorScope }: DeviceComparisonProps) {
  const companyItems = companyScope?.signals ?? [];
  const competitorItems = competitorScope?.signals ?? [];
  return (
    <div className="rounded-md border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-foreground">Device Signals</h3>
        <InformationPopover ariaLabel="About device signals" title="Device Signals">
          <p><strong>mobile_new_activity:</strong> mobile traffic appears in the second period half.</p>
          <p><strong>mobile_growth_low_quality:</strong> mobile grows while its quality trails desktop.</p>
          <p><strong>desktop_quality_advantage:</strong> desktop has a meaningful quality advantage.</p>
          <p><strong>mobile_strength:</strong> mobile leads traffic with comparable or better quality.</p>
          <p><strong>balanced_device_quality:</strong> desktop and mobile quality differ by less than 10%.</p>
          <p className="mt-2"><strong>low:</strong> informative condition. <strong>medium:</strong> material condition worth monitoring.</p>
        </InformationPopover>
      </div>
      <div className="mt-3 grid gap-3">
        {companyItems.length === 0 && competitorItems.length === 0 ? <p className="text-sm text-muted-foreground">No device signals detected.</p> : null}
        <SignalItems items={companyItems} tone={combinedScopes ? 'neutral' : 'company'} />
        <SignalItems items={competitorItems} tone="competitor" />
      </div>
    </div>
  );
}
