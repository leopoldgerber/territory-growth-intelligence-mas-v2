import { InformationPopover } from '@/components/dashboard/information-popover';

import { ComparisonValue, type ChannelComparisonProps } from './channel-comparison';

const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

export function ChannelMixCard({ combinedScopes, companyScope, competitorScope }: ChannelComparisonProps) {
  const companyItems = new Map((companyScope?.channel_mix ?? []).map((item) => [item.channel, item]));
  const competitorItems = new Map((competitorScope?.channel_mix ?? []).map((item) => [item.channel, item]));
  const channels = Array.from(new Set([...companyItems.keys(), ...competitorItems.keys()]));

  return (
    <div className="rounded-md border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-foreground">Channel Mix</h3>
        <InformationPopover ariaLabel="About channel mix" title="Channel Mix">
          Distribution of total traffic across direct, search, paid, referral, and social channels for this scope.
        </InformationPopover>
      </div>
      <div className="mt-4 grid gap-4">
        {channels.length === 0 ? <p className="text-sm text-muted-foreground">No channel data available.</p> : null}
        {channels.map((channel) => {
          const companyItem = companyItems.get(channel);
          const competitorItem = competitorItems.get(channel);
          return (
          <div className="grid gap-1.5" key={channel}>
            <div className="flex items-center justify-between gap-3 text-xs">
              <span className="font-medium text-foreground">{format_label(channel)}</span>
              <ComparisonValue
                combinedScopes={combinedScopes}
                companyValue={companyItem ? `${numberFormatter.format(companyItem.traffic)} / ${percentFormatter.format(companyItem.share)}` : null}
                competitorValue={competitorItem ? `${numberFormatter.format(competitorItem.traffic)} / ${percentFormatter.format(competitorItem.share)}` : null}
              />
            </div>
            <div className="grid gap-1">
              {companyItem ? (
                <div className="h-1.5 overflow-hidden rounded-sm bg-secondary">
                  <div className={combinedScopes ? 'h-full bg-primary' : 'h-full bg-emerald-500'} style={{ width: `${Math.min(companyItem.share * 100, 100)}%` }} />
                </div>
              ) : null}
              {competitorItem ? (
                <div className="h-1.5 overflow-hidden rounded-sm bg-secondary">
                  <div className="h-full bg-sky-500" style={{ width: `${Math.min(competitorItem.share * 100, 100)}%` }} />
                </div>
              ) : null}
            </div>
          </div>
          );
        })}
      </div>
    </div>
  );
}
