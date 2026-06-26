import { InformationPopover } from '@/components/dashboard/information-popover';
import { SortableTableHeader } from '@/components/dashboard/sortable-table-header';
import { Badge } from '@/components/ui/badge';
import { useTableSort, type SortColumn } from '@/lib/dashboard/table-sorting';
import type { OpportunityScore, OpportunityScoreCategory, OpportunityScoreFactorBreakdown } from '@/lib/types/analytics';
import type { ReactNode } from 'react';


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

const headerDescriptions: Record<string, ReactNode> = {
  Rank: 'Position inside the corresponding overall, company, or competitor scope.',
  Country: 'Country evaluated from the selected Dashboard data.',
  Scope: 'Overall is neutral; Company is green; Competitor is blue.',
  Score: 'Weighted analytical score from 0 to 100 across eight factors.',
  Category: (
    <>
      <p>Score status.</p>
      <p><strong>very_high:</strong> 80-100.</p>
      <p><strong>high:</strong> 65-79.9999.</p>
      <p><strong>medium:</strong> 50-64.9999.</p>
      <p><strong>low:</strong> 35-49.9999.</p>
      <p><strong>very_low:</strong> 0-34.9999.</p>
    </>
  ),
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

type ScoringSortKey =
  | 'category'
  | 'competition_level'
  | 'concentration'
  | 'country'
  | 'entry_risk'
  | 'growth'
  | 'market_size'
  | 'opportunity_score'
  | 'position_potential'
  | 'rank'
  | 'scope'
  | 'traffic_quality'
  | 'channel_stability';

function ScoringHeader({
  activeKey,
  align = 'right',
  label,
  onSort,
  sortDirection,
  sortKey,
}: {
  activeKey: ScoringSortKey;
  align?: 'left' | 'right';
  label: string;
  onSort: (key: ScoringSortKey) => void;
  sortDirection: 'asc' | 'desc';
  sortKey: ScoringSortKey;
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
  const columns: SortColumn<OpportunityScore, ScoringSortKey>[] = [
    { key: 'rank', getValue: (item) => item.rank ?? 0 },
    { key: 'country', getValue: (item) => item.country },
    { key: 'scope', getValue: (item) => item.scope },
    { key: 'opportunity_score', getValue: (item) => item.opportunity_score },
    { key: 'category', getValue: (item) => item.score_category },
    ...Object.keys(factorLabels).map((factor) => ({
      key: factor as ScoringSortKey,
      getValue: (item: OpportunityScore) => item.factor_scores[factor] ?? 0,
    })),
  ];
  const { requestSort, sortedRows, sortState } = useTableSort(items, columns, {
    direction: 'asc',
    key: 'rank',
  });

  return (
    <div className="overflow-hidden rounded-md border bg-background">
      <table className="w-full table-fixed text-xs">
        <thead className="bg-secondary text-muted-foreground">
          <tr>
            <ScoringHeader activeKey={sortState.key} align="left" label="Rank" onSort={requestSort} sortDirection={sortState.direction} sortKey="rank" />
            <ScoringHeader activeKey={sortState.key} align="left" label="Country" onSort={requestSort} sortDirection={sortState.direction} sortKey="country" />
            <ScoringHeader activeKey={sortState.key} align="left" label="Scope" onSort={requestSort} sortDirection={sortState.direction} sortKey="scope" />
            <ScoringHeader activeKey={sortState.key} label="Score" onSort={requestSort} sortDirection={sortState.direction} sortKey="opportunity_score" />
            <ScoringHeader activeKey={sortState.key} align="left" label="Category" onSort={requestSort} sortDirection={sortState.direction} sortKey="category" />
            {Object.entries(factorLabels).map(([factor, label]) => (
              <ScoringHeader activeKey={sortState.key} key={label} label={label} onSort={requestSort} sortDirection={sortState.direction} sortKey={factor as ScoringSortKey} />
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((item) => {
            const key = `${item.scope}-${item.country_id}`;
            const valueClass = scope_class(item.scope);
            return (
              <tr className={`border-t ${selectedKey === key ? 'bg-secondary/60' : ''}`} key={key}>
                <td className="px-2 py-2 text-muted-foreground">{item.rank ?? '-'}</td>
                <td className="px-2 py-2">
                  <button className={`break-words text-left font-medium leading-4 hover:underline ${valueClass}`} onClick={() => onSelect(key)} type="button">
                    <span>{item.country}</span>
                    <span className="block text-[11px] text-muted-foreground">{item.country_code}</span>
                  </button>
                </td>
                <td className={`break-words px-2 py-2 font-medium ${valueClass}`}>{format_label(item.scope)}</td>
                <td className={`px-2 py-2 text-right font-semibold ${valueClass}`}>{scoreFormatter.format(item.opportunity_score)}</td>
                <td className="px-2 py-2"><Badge className="whitespace-normal break-words text-[11px]" variant={category_variant(item.score_category)}>{format_label(item.score_category)}</Badge></td>
                {Object.keys(factorLabels).map((factor) => (
                  <td className={`px-2 py-2 text-right ${valueClass}`} key={factor}>
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

function FactorBreakdownTable({ factors }: { factors: OpportunityScoreFactorBreakdown[] }) {
  type FactorSortKey = 'explanation' | 'factor' | 'raw_value' | 'score' | 'status' | 'weight' | 'weighted_score';
  const columns: SortColumn<OpportunityScoreFactorBreakdown, FactorSortKey>[] = [
    { key: 'factor', getValue: (factor) => factorLabels[factor.factor] ?? format_label(factor.factor) },
    { key: 'raw_value', getValue: (factor) => format_raw(factor) },
    { key: 'score', getValue: (factor) => factor.score },
    { key: 'weight', getValue: (factor) => factor.weight },
    { key: 'weighted_score', getValue: (factor) => factor.weighted_score },
    { key: 'status', getValue: (factor) => factor.status },
    { key: 'explanation', getValue: (factor) => factor.explanation },
  ];
  const { requestSort, sortedRows, sortState } = useTableSort(factors, columns, {
    direction: 'desc',
    key: 'weighted_score',
  });

  return (
    <div className="overflow-hidden rounded-md border bg-background">
      <table className="w-full table-fixed text-xs">
        <thead className="bg-secondary text-muted-foreground">
          <tr>
            <SortableTableHeader activeKey={sortState.key} label="Factor" onSort={requestSort} sortDirection={sortState.direction} sortKey="factor" />
            <SortableTableHeader activeKey={sortState.key} label="Raw Value" onSort={requestSort} sortDirection={sortState.direction} sortKey="raw_value" />
            <SortableTableHeader activeKey={sortState.key} align="right" label="Score" onSort={requestSort} sortDirection={sortState.direction} sortKey="score" />
            <SortableTableHeader activeKey={sortState.key} align="right" label="Weight" onSort={requestSort} sortDirection={sortState.direction} sortKey="weight" />
            <SortableTableHeader activeKey={sortState.key} align="right" label="Weighted Score" onSort={requestSort} sortDirection={sortState.direction} sortKey="weighted_score" />
            <SortableTableHeader activeKey={sortState.key} label="Status" onSort={requestSort} sortDirection={sortState.direction} sortKey="status">
              <InformationPopover ariaLabel="About factor statuses" title="Factor Status">
                <p><strong>strong:</strong> factor score is at least 75.</p>
                <p><strong>moderate:</strong> factor score is above 40 and below 75.</p>
                <p><strong>weak:</strong> factor score is 40 or lower.</p>
                <p><strong>not_available:</strong> source data is missing and a neutral fallback is used.</p>
              </InformationPopover>
            </SortableTableHeader>
            <SortableTableHeader activeKey={sortState.key} label="Explanation" onSort={requestSort} sortDirection={sortState.direction} sortKey="explanation" />
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((factor) => (
            <tr className="border-t align-top" key={factor.factor}>
              <td className="break-words px-2 py-2 font-medium text-foreground">{factorLabels[factor.factor] ?? format_label(factor.factor)}</td>
              <td className="break-words px-2 py-2 text-muted-foreground">{format_raw(factor)}</td>
              <td className="px-2 py-2 text-right">{scoreFormatter.format(factor.score)}</td>
              <td className="px-2 py-2 text-right">{percentFormatter.format(factor.weight)}</td>
              <td className="px-2 py-2 text-right">{scoreFormatter.format(factor.weighted_score)}</td>
              <td className="px-2 py-2"><Badge className="whitespace-normal break-words text-[11px]" variant="outline">{format_label(factor.status)}</Badge></td>
              <td className="break-words px-2 py-2 leading-5 text-muted-foreground">{factor.explanation}</td>
            </tr>
          ))}
        </tbody>
      </table>
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

      <FactorBreakdownTable factors={item.explanation.factor_breakdown} />

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
