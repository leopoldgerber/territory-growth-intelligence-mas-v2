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
          Neutral rule-based comparisons of desktop and mobile traffic quality. They are analytical signals, not recommendations or final scoring.
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
