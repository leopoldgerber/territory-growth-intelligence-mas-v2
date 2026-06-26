import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';
import type { BudgetChannelRole, BudgetStrategyReport } from '@/lib/types/reports';


const amountFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const percentFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1, style: 'percent' });
const scoreFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

function role_variant(role: BudgetChannelRole): 'default' | 'secondary' | 'warning' | 'destructive' {
  if (role === 'priority') return 'default';
  if (role === 'risky') return 'destructive';
  if (role === 'test') return 'warning';
  return 'secondary';
}

function ValueList({ items }: { items: string[] }) {
  return items.length ? <ul className="mt-2 grid gap-1 text-sm text-muted-foreground">{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="mt-2 text-sm text-muted-foreground">None.</p>;
}

export function BudgetStrategyReportView({ report }: { report: BudgetStrategyReport }) {
  const warnings = report.explanation.warnings ?? [];
  return (
    <div className="space-y-5">
      {warnings.length ? <div className="rounded-md border border-amber-500/40 bg-amber-500/5 p-4"><p className="text-sm font-medium text-foreground">Fallback notes</p><ValueList items={warnings} /></div> : null}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
        {[
          ['Country', `${report.country} (${report.country_code})`],
          ['Period', `${report.date_from} - ${report.date_to}`],
          ['Budget', `${amountFormatter.format(report.budget_amount)} ${report.currency}`],
          ['Scope', format_label(report.scope)],
          ['Opportunity Score', report.opportunity_score === null ? 'Fallback' : scoreFormatter.format(report.opportunity_score)],
          ['Generated', new Date(report.created_at).toLocaleString()],
        ].map(([label, value]) => <div className="rounded-md border bg-background p-4" key={label}><p className="text-xs text-muted-foreground">{label}</p><p className="mt-2 text-sm font-semibold text-foreground">{value}</p></div>)}
      </div>

      <div className="rounded-md border bg-background p-4">
        <div className="flex items-center gap-2"><h3 className="text-sm font-semibold">Marketing Recommendation</h3><InformationPopover ariaLabel="About the recommendation" title="Recommendation limitation">Directional, rule-based guidance from traffic and quality signals. It does not predict ROI, CPA, revenue, conversions, or customer counts.</InformationPopover></div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">{report.recommended_approach}</p>
      </div>

      <div className="overflow-hidden rounded-md border bg-background">
        <table className="w-full table-fixed text-sm">
          <thead className="bg-secondary text-muted-foreground"><tr><th className="px-3 py-2 text-left">Channel</th><th className="px-3 py-2 text-left">Role</th><th className="px-3 py-2 text-right">Share</th><th className="px-3 py-2 text-right">Amount</th><th className="px-3 py-2 text-left">Reason</th></tr></thead>
          <tbody>{report.allocation.map((item) => <tr className="border-t" key={item.channel}><td className="break-words px-3 py-2 font-medium">{format_label(item.channel)}</td><td className="px-3 py-2"><Badge className="whitespace-normal break-words text-[11px]" variant={role_variant(item.role)}>{item.role}</Badge></td><td className="px-3 py-2 text-right">{percentFormatter.format(item.share)}</td><td className="break-words px-3 py-2 text-right">{amountFormatter.format(item.amount)} {report.currency}</td><td className="break-words px-3 py-2 text-xs text-muted-foreground">{item.reason}</td></tr>)}</tbody>
        </table>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        {(['priority', 'test', 'supporting', 'risky'] as BudgetChannelRole[]).map((role) => <div className="rounded-md border bg-background p-4" key={role}><div className="flex items-center justify-between"><h3 className="text-sm font-semibold">{format_label(role)} Channels</h3><Badge variant={role_variant(role)}>{role}</Badge></div><ValueList items={(report.channel_roles[role] ?? []).map(format_label)} /></div>)}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-md border bg-background p-4"><h3 className="text-sm font-semibold">Expected Directional Effect</h3><p className="mt-2 text-xs text-muted-foreground">Confidence: {format_label(report.expected_effect.confidence)} / Direction: {format_label(report.expected_effect.expected_direction)}</p><h4 className="mt-4 text-xs font-medium">Primary effects</h4><ValueList items={report.expected_effect.primary_effects} /><h4 className="mt-4 text-xs font-medium">Secondary effects</h4><ValueList items={report.expected_effect.secondary_effects} /><h4 className="mt-4 text-xs font-medium">Measurement focus</h4><ValueList items={report.expected_effect.measurement_focus} /></div>
        <div className="rounded-md border bg-background p-4"><h3 className="text-sm font-semibold">Strategy Risks</h3>{report.risks.length ? <div className="mt-3 grid gap-3">{report.risks.map((risk) => <div className="border-l-2 border-amber-500 pl-3" key={risk.type}><div className="flex gap-2"><span className="text-sm font-medium">{format_label(risk.type)}</span><Badge variant={risk.severity === 'high' ? 'destructive' : 'warning'}>{risk.severity}</Badge></div><p className="mt-1 text-xs text-muted-foreground">{risk.message}</p><p className="mt-1 text-xs text-muted-foreground">Affected: {risk.affected_channels.map(format_label).join(', ')}</p><p className="mt-1 text-xs">{risk.mitigation_hint}</p></div>)}</div> : <p className="mt-3 text-sm text-muted-foreground">No elevated rule-based risks detected.</p>}</div>
      </div>

      <details className="rounded-md border bg-background p-4"><summary className="cursor-pointer text-sm font-semibold">Source analytics used</summary><pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap text-xs text-muted-foreground">{JSON.stringify(report.source_snapshot, null, 2)}</pre></details>
    </div>
  );
}
