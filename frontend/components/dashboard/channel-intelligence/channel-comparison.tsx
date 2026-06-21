import type { ReactNode } from 'react';

import type { ChannelScopeAnalytics } from '@/lib/types/analytics';


export type ChannelComparisonProps = {
  combinedScopes: boolean;
  companyScope: ChannelScopeAnalytics | null;
  competitorScope: ChannelScopeAnalytics | null;
};

export function ComparisonValue({
  combinedScopes,
  companyValue,
  competitorValue,
  className = '',
}: {
  combinedScopes: boolean;
  companyValue: ReactNode | null;
  competitorValue: ReactNode | null;
  className?: string;
}) {
  if (combinedScopes) {
    return <span className={`text-foreground ${className}`}>{companyValue}</span>;
  }

  return (
    <span className={`inline-flex flex-wrap items-center justify-end gap-1.5 ${className}`}>
      {companyValue !== null ? <span className="text-emerald-500">{companyValue}</span> : null}
      {companyValue !== null && competitorValue !== null ? <span className="text-muted-foreground">|</span> : null}
      {competitorValue !== null ? <span className="text-sky-500">{competitorValue}</span> : null}
    </span>
  );
}

export function ChannelLegend({ combinedScopes }: { combinedScopes: boolean }) {
  if (combinedScopes) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-sm bg-emerald-500" /> Company
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-sm bg-sky-500" /> Competitors
      </span>
    </div>
  );
}
