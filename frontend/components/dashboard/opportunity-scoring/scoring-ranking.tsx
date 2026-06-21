import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';
import type { OpportunityScore, OpportunityScoreCategory, OpportunityScoreFactorBreakdown } from '@/lib/types/analytics';


const scoreFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });
const percentFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1, style: 'percent' });

const factorLabels: Record<string, string> = {
  market_size: 'Market Size',
  growth: 'Growth',
  traffic_quality: 'Quality',
  competition_level: 'Competition',
  concentration: 'Concentration',
  channel_stability: 'Channel Stability',
  entry_risk: 'Entry Risk',
  position_potential: 'Position Potential',
};

const headerDescriptions: Record<string, string> = {
  Rank: 'Position inside the corresponding overall, company, or competitor scope.',
  Country: 'Country evaluated from the selected Dashboard data.',
  Scope: 'Overall is neutral; Company is green; Competitor is blue.',
  Score: 'Weighted analytical score from 0 to 100 across eight factors.',
  Category: 'Very High: 80-100; High: 65-79.9999; Medium: 50-64.9999; Low: 35-49.9999; Very Low: 0-34.9999.',
  'Market Size': 'Traffic percentile among countries in the same scope.',
  Growth: 'Traffic movement between the first and second period halves.',
  Quality: 'Weighted duration, no-bounce rate, and pages per visit.',
  Competition: 'Score based on active company density and market size.',
  Concentration: 'Opportunity impact of top-1 and top-3 company traffic shares.',
  'Channel Stability': 'Score derived from channel-shift signals, with a neutral fallback when unavailable.',
  'Entry Risk': 'Inverted score: fewer and weaker risk signals produce a higher value.',
  'Position Potential': 'Positive-signal bonus added to a neutral baseline.',
};

function category_variant(category: OpportunityScoreCategory): 'success' | 'default' | 'secondary' | 'warning' {
  if (category === 'very_high') {
    return 'success';
  }
  if (category === 'high') {
    return 'default';
  }
  if (category === 'low' || category === 'very_low') {
    return 'warning';
  }
  return 'secondary';
}

function scope_class(scope: string): string {
  if (scope === 'company') {
    return 'text-emerald-500';
  }
  if (scope === 'competitor') {
    return 'text-sky-500';
  }
  return 'text-foreground';
}

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

function ScoringHeader({ label, align = 'right' }: { label: string; align?: 'left' | 'right' }) {
  return (
    <th className={`px-3 py-2 font-medium ${align === 'right' ? 'text-right' : 'text-left'}`}>
      <span className={`flex items-center gap-1 ${align === 'right' ? 'justify-end' : 'justify-start'}`}>
        {label}
        <InformationPopover ariaLabel={`About ${label.toLowerCase()}`} title={label}>
          {headerDescriptions[label]}
        </InformationPopover>
      </span>
    </th>
  );
}

function format_raw(factor: OpportunityScoreFactorBreakdown): string {
  if (factor.raw_value === null || factor.raw_value === undefined) {
    return 'None';
  }
  if (typeof factor.raw_value === 'number') {
    return scoreFormatter.format(factor.raw_value);
  }
  if (Array.isArray(factor.raw_value)) {
    return factor.raw_value.map(String).join(', ') || 'None';
  }
  if (typeof factor.raw_value === 'object') {
    return Object.entries(factor.raw_value as Record<string, unknown>)
      .map(([key, value]) => `${format_label(key)}: ${typeof value === 'number' ? scoreFormatter.format(value) : String(value)}`)
      .join('; ');
  }
  return String(factor.raw_value);
}

export function ScoringRankingTable({
  items,
  selectedKey,
  onSelect,
}: {
  items: OpportunityScore[];
  selectedKey: string;
  onSelect: (key: string) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-md border bg-background">
      <table className="w-full min-w-[1500px] text-sm">
        <thead className="bg-secondary text-muted-foreground">
          <tr>
            <ScoringHeader align="left" label="Rank" />
            <ScoringHeader align="left" label="Country" />
            <ScoringHeader align="left" label="Scope" />
            <ScoringHeader label="Score" />
            <ScoringHeader align="left" label="Category" />
            {Object.values(factorLabels).map((label) => <ScoringHeader key={label} label={label} />)}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const key = `${item.scope}-${item.country_id}`;
            const valueClass = scope_class(item.scope);
            return (
              <tr className={`border-t ${selectedKey === key ? 'bg-secondary/60' : ''}`} key={key}>
                <td className="px-3 py-2 text-muted-foreground">{item.rank ?? '-'}</td>
                <td className="px-3 py-2">
                  <button className={`font-medium hover:underline ${valueClass}`} onClick={() => onSelect(key)} type="button">
                    {item.country} <span className="text-xs text-muted-foreground">{item.country_code}</span>
                  </button>
                </td>
                <td className={`px-3 py-2 font-medium ${valueClass}`}>{format_label(item.scope)}</td>
                <td className={`px-3 py-2 text-right text-base font-semibold ${valueClass}`}>{scoreFormatter.format(item.opportunity_score)}</td>
                <td className="px-3 py-2"><Badge variant={category_variant(item.score_category)}>{format_label(item.score_category)}</Badge></td>
                {Object.keys(factorLabels).map((factor) => (
                  <td className={`px-3 py-2 text-right ${valueClass}`} key={factor}>
                    {scoreFormatter.format(item.factor_scores[factor] ?? 0)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function DetailList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border bg-background p-4">
      <h4 className="text-sm font-semibold text-foreground">{title}</h4>
      {items.length ? (
        <ul className="mt-3 grid gap-2 text-sm text-muted-foreground">
          {items.map((item) => <li key={item}>{item}</li>)}
        </ul>
      ) : <p className="mt-3 text-sm text-muted-foreground">None detected.</p>}
    </div>
  );
}

export function ScoringDetail({ item }: { item: OpportunityScore }) {
  return (
    <div className="space-y-4 border-t pt-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className={`text-base font-semibold ${scope_class(item.scope)}`}>{item.country} score detail</h3>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{item.explanation.summary}</p>
        </div>
        <div className="text-right">
          <p className={`text-2xl font-semibold ${scope_class(item.scope)}`}>{scoreFormatter.format(item.opportunity_score)}</p>
          <Badge variant={category_variant(item.score_category)}>{format_label(item.score_category)}</Badge>
        </div>
      </div>

      <div className="overflow-x-auto rounded-md border bg-background">
        <table className="w-full min-w-[900px] text-sm">
          <thead className="bg-secondary text-muted-foreground">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Factor</th>
              <th className="px-3 py-2 text-left font-medium">Raw Value</th>
              <th className="px-3 py-2 text-right font-medium">Score</th>
              <th className="px-3 py-2 text-right font-medium">Weight</th>
              <th className="px-3 py-2 text-right font-medium">Weighted Score</th>
              <th className="px-3 py-2 text-left font-medium">
                <span className="flex items-center gap-1">
                  Status
                  <InformationPopover ariaLabel="About factor statuses" title="Factor Status">
                    <p><strong>strong:</strong> factor score is at least 75.</p>
                    <p><strong>moderate:</strong> factor score is above 40 and below 75.</p>
                    <p><strong>weak:</strong> factor score is 40 or lower.</p>
                    <p><strong>not_available:</strong> source data is missing and a neutral fallback is used.</p>
                  </InformationPopover>
                </span>
              </th>
              <th className="px-3 py-2 text-left font-medium">Explanation</th>
            </tr>
          </thead>
          <tbody>
            {item.explanation.factor_breakdown.map((factor) => (
              <tr className="border-t align-top" key={factor.factor}>
                <td className="px-3 py-2 font-medium text-foreground">{factorLabels[factor.factor] ?? format_label(factor.factor)}</td>
                <td className="max-w-xs px-3 py-2 text-xs text-muted-foreground">{format_raw(factor)}</td>
                <td className="px-3 py-2 text-right">{scoreFormatter.format(factor.score)}</td>
                <td className="px-3 py-2 text-right">{percentFormatter.format(factor.weight)}</td>
                <td className="px-3 py-2 text-right">{scoreFormatter.format(factor.weighted_score)}</td>
                <td className="px-3 py-2"><Badge variant="outline">{format_label(factor.status)}</Badge></td>
                <td className="max-w-md px-3 py-2 text-xs leading-5 text-muted-foreground">{factor.explanation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <DetailList items={item.strengths} title="Strengths" />
        <DetailList items={item.weaknesses} title="Weaknesses" />
        <DetailList items={item.risks} title="Risks" />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <h4 className="text-sm font-semibold text-foreground">Signals Used</h4>
          <p className="mt-2 text-sm text-muted-foreground">{item.explanation.signals_used.map(format_label).join(', ') || 'None'}</p>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-foreground">Fallbacks Used</h4>
          <p className="mt-2 text-sm text-muted-foreground">{item.explanation.fallbacks_used.map(format_label).join(', ') || 'None'}</p>
        </div>
      </div>
    </div>
  );
}
