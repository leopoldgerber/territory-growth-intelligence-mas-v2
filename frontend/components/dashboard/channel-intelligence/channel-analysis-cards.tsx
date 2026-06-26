import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';
import type {
  ChannelSkew,
  OpportunitySignal,
  SourceBreakdownItem,
  TrafficBreakdownItem,
} from '@/lib/types/analytics';

import { ComparisonValue, type ChannelComparisonProps } from './channel-comparison';
import { channelBorderClasses, channelValueClasses, type ChannelScopeTone } from './channel-scope-style';


const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

export function PaidOrganicCard({ combinedScopes, companyScope, competitorScope }: ChannelComparisonProps) {
  const items = [
    { label: 'Paid', traffic: 'paid_traffic', share: 'paid_share', opacity: 'opacity-100' },
    { label: 'Organic', traffic: 'organic_traffic', share: 'organic_share', opacity: 'opacity-60' },
    { label: 'Unknown', traffic: 'unknown_traffic', share: 'unknown_share', opacity: 'opacity-30' },
  ] as const;

  return (
    <div className="rounded-md border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-foreground">Paid / Organic</h3>
        <InformationPopover ariaLabel="About paid and organic traffic" title="Paid / Organic">
          <p>Journey traffic classified by acquisition payment type. Shares use total classified journey traffic.</p>
          <p><strong>Paid:</strong> traffic from paid acquisition sources.</p>
          <p><strong>Organic:</strong> traffic from non-paid acquisition sources.</p>
          <p><strong>Unknown:</strong> traffic where paid or organic classification is unavailable.</p>
        </InformationPopover>
      </div>
      <div className="mt-4 grid gap-3">
        {items.map((item) => {
          const companyData = companyScope?.paid_organic;
          const competitorData = competitorScope?.paid_organic;
          const companyShare = companyData?.[item.share] ?? null;
          const competitorShare = competitorData?.[item.share] ?? null;
          return (
            <div className="grid gap-1" key={item.label}>
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="text-muted-foreground">{item.label}</span>
                <ComparisonValue
                  combinedScopes={combinedScopes}
                  companyValue={companyData ? `${numberFormatter.format(companyData[item.traffic])} / ${percentFormatter.format(companyData[item.share])}` : null}
                  competitorValue={competitorData ? `${numberFormatter.format(competitorData[item.traffic])} / ${percentFormatter.format(competitorData[item.share])}` : null}
                />
              </div>
              {companyShare !== null ? (
                <div className="h-1.5 overflow-hidden rounded-sm bg-secondary">
                  <div className={`${combinedScopes ? 'bg-primary' : 'bg-emerald-500'} h-full ${item.opacity}`} style={{ width: `${Math.min(companyShare * 100, 100)}%` }} />
                </div>
              ) : null}
              {competitorShare !== null ? (
                <div className="h-1.5 overflow-hidden rounded-sm bg-secondary">
                  <div className={`h-full bg-sky-500 ${item.opacity}`} style={{ width: `${Math.min(competitorShare * 100, 100)}%` }} />
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

type BreakdownCardProps = ChannelComparisonProps & {
  title: string;
  type: 'source' | 'traffic';
};

function item_label(item: SourceBreakdownItem | TrafficBreakdownItem): string {
  return 'source_type' in item ? item.source_type : item.traffic_type;
}

export function BreakdownCard({ combinedScopes, companyScope, competitorScope, title, type }: BreakdownCardProps) {
  const companyItems = type === 'source' ? companyScope?.source_type_breakdown ?? [] : companyScope?.traffic_type_breakdown ?? [];
  const competitorItems = type === 'source' ? competitorScope?.source_type_breakdown ?? [] : competitorScope?.traffic_type_breakdown ?? [];
  const companyMap = new Map(companyItems.map((item) => [item_label(item), item]));
  const competitorMap = new Map(competitorItems.map((item) => [item_label(item), item]));
  const labels = Array.from(new Set([...companyMap.keys(), ...competitorMap.keys()]));

  return (
    <div className="rounded-md border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <InformationPopover ariaLabel={`About ${title.toLowerCase()}`} title={title}>
          {type === 'source' ? (
            <p>Journey traffic grouped by acquisition source type with traffic totals and shares.</p>
          ) : (
            <>
              <p>Journey traffic grouped by traffic classification.</p>
              <p><strong>paid:</strong> traffic from paid acquisition sources.</p>
              <p><strong>organic:</strong> traffic from non-paid acquisition sources.</p>
              <p><strong>unknown:</strong> traffic where classification is unavailable.</p>
            </>
          )}
        </InformationPopover>
      </div>
      <div className="mt-4 grid gap-3">
        {labels.length === 0 ? <p className="text-sm text-muted-foreground">No journey data available.</p> : null}
        {labels.map((label) => {
          const companyItem = companyMap.get(label);
          const competitorItem = competitorMap.get(label);
          return (
            <div className="grid gap-1" key={label}>
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="font-medium text-foreground">{format_label(label)}</span>
                <ComparisonValue
                  combinedScopes={combinedScopes}
                  companyValue={companyItem ? `${numberFormatter.format(companyItem.traffic)} / ${percentFormatter.format(companyItem.share)}` : null}
                  competitorValue={competitorItem ? `${numberFormatter.format(competitorItem.traffic)} / ${percentFormatter.format(competitorItem.share)}` : null}
                />
              </div>
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
          );
        })}
      </div>
    </div>
  );
}

function ScopedItems<T>({
  combinedScopes,
  companyItems,
  competitorItems,
  emptyText,
  renderItem,
}: {
  combinedScopes: boolean;
  companyItems: T[];
  competitorItems: T[];
  emptyText: string;
  renderItem: (item: T, tone: ChannelScopeTone, index: number) => React.ReactNode;
}) {
  if (companyItems.length === 0 && competitorItems.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyText}</p>;
  }

  return (
    <>
      {companyItems.map((item, index) => renderItem(item, combinedScopes ? 'neutral' : 'company', index))}
      {competitorItems.map((item, index) => renderItem(item, 'competitor', index))}
    </>
  );
}

export function ChannelSkewsCard({ combinedScopes, companyScope, competitorScope }: ChannelComparisonProps) {
  const renderItem = (item: ChannelSkew, tone: ChannelScopeTone, index: number) => (
    <div className={`border-l-2 pl-3 ${channelBorderClasses[tone]}`} key={`${tone}-${item.company}-${item.signal}-${index}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`text-sm font-medium ${channelValueClasses[tone]}`}>{item.company}</span>
        <Badge variant="outline">{format_label(item.signal)}</Badge>
        <span className={`text-xs ${channelValueClasses[tone]}`}>{percentFormatter.format(item.share)}</span>
      </div>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.message}</p>
    </div>
  );

  return (
    <div className="rounded-md border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-foreground">Channel Skews</h3>
        <InformationPopover ariaLabel="About channel skews" title="Channel Skews">
          <p>These statuses describe channel concentration or balance inside a company channel mix.</p>
          <p><strong>brand_dependency:</strong> direct traffic is at least 60%.</p>
          <p><strong>seo_dependency:</strong> search traffic is at least 60%.</p>
          <p><strong>paid_dependency:</strong> paid traffic is at least 35%.</p>
          <p><strong>referral_dependency:</strong> referral traffic is at least 30%.</p>
          <p><strong>social_dependency:</strong> social traffic is at least 25%.</p>
          <p><strong>balanced_mix:</strong> no channel reaches a 40% share.</p>
        </InformationPopover>
      </div>
      <div className="mt-3 grid gap-3">
        <ScopedItems
          combinedScopes={combinedScopes}
          companyItems={companyScope?.channel_skews ?? []}
          competitorItems={competitorScope?.channel_skews ?? []}
          emptyText="No channel skews detected."
          renderItem={renderItem}
        />
      </div>
    </div>
  );
}

export function OpportunitySignalsCard({ combinedScopes, companyScope, competitorScope }: ChannelComparisonProps) {
  const renderItem = (item: OpportunitySignal, tone: ChannelScopeTone, index: number) => (
    <div className={`border-l-2 pl-3 ${channelBorderClasses[tone]}`} key={`${tone}-${item.signal}-${index}`}>
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">{format_label(item.type)}</Badge>
        <span className={`text-xs font-medium ${channelValueClasses[tone]}`}>{format_label(item.signal)}</span>
      </div>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.message}</p>
    </div>
  );

  return (
    <div className="rounded-md border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-foreground">Opportunity Signals</h3>
        <InformationPopover ariaLabel="About opportunity signals" title="Opportunity Signals">
          <p>Each item has a type badge and a specific signal value.</p>
          <div className="mt-3 grid gap-2">
            <div>
              <p className="font-medium text-foreground">Types</p>
              <p><strong>seo:</strong> search is a material acquisition direction.</p>
              <p><strong>paid:</strong> paid acquisition has meaningful presence.</p>
              <p><strong>partnerships:</strong> referral traffic may indicate partnership-driven acquisition.</p>
              <p><strong>social:</strong> social traffic has meaningful presence.</p>
              <p><strong>brand:</strong> direct traffic is a major acquisition channel.</p>
              <p><strong>channel_gap:</strong> a channel is nearly absent and may represent a gap or unused route.</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Signals</p>
              <p><strong>high_search_share:</strong> search represents at least 40%.</p>
              <p><strong>meaningful_paid_share:</strong> paid represents at least 20%.</p>
              <p><strong>visible_referral_share:</strong> referral represents at least 15%.</p>
              <p><strong>visible_social_share:</strong> social represents at least 15%.</p>
              <p><strong>high_direct_share:</strong> direct represents at least 50%.</p>
              <p><strong>low_*_share:</strong> the named channel represents 3% or less.</p>
            </div>
          </div>
        </InformationPopover>
      </div>
      <div className="mt-3 grid gap-3">
        <ScopedItems
          combinedScopes={combinedScopes}
          companyItems={companyScope?.opportunity_signals ?? []}
          competitorItems={competitorScope?.opportunity_signals ?? []}
          emptyText="No channel signals detected."
          renderItem={renderItem}
        />
      </div>
    </div>
  );
}
