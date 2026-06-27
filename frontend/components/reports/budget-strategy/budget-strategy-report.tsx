import { InformationPopover } from '@/components/dashboard/information-popover';
import { Badge } from '@/components/ui/badge';
import type { BudgetChannelRole, BudgetStrategyReport } from '@/lib/types/reports';


const amountFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const percentFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1, style: 'percent' });
const scoreFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });
const channels = ['direct', 'search', 'paid', 'referral', 'social'];

type JsonRecord = Record<string, unknown>;

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

function read_record(value: unknown): JsonRecord {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as JsonRecord : {};
}

function read_string(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null;
}

function read_number(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function format_value(value: unknown): string {
  const numberValue = read_number(value);
  if (numberValue !== null) return scoreFormatter.format(numberValue);
  const stringValue = read_string(value);
  return stringValue ? format_label(stringValue) : 'Unavailable';
}

function format_share(value: unknown): string {
  const numberValue = read_number(value);
  return numberValue === null ? 'Unavailable' : percentFormatter.format(numberValue);
}

function format_opportunity_score(report: BudgetStrategyReport): string {
  const status = report.dependency_status.opportunity_score.status;
  const score = report.dependency_status.opportunity_score.score ?? report.opportunity_score;
  if (status === 'failed' || score === null) return 'Unavailable';
  const label = scoreFormatter.format(score);
  if (status === 'fallback_used' || report.dependency_status.opportunity_score.is_fallback) {
    return `${label} · fallback-derived`;
  }
  return label;
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

function MetricRow({ label, value }: { label: string; value: string }) {
  return <div className="flex items-start justify-between gap-3 text-xs"><span className="text-muted-foreground">{label}</span><span className="max-w-[55%] break-words text-right font-medium text-foreground">{value}</span></div>;
}

export function BudgetStrategyReportView({ report }: { report: BudgetStrategyReport }) {
  const warnings = report.explanation.warnings ?? [];
  const marketEntryNoData = report.explanation.market_entry_no_target_country_data === true;
  const deviceNote = typeof report.explanation.device_note === 'string' ? report.explanation.device_note : null;
  const sourceSnapshot = read_record(report.source_snapshot);
  const channelIntelligence = read_record(sourceSnapshot.channel_intelligence);
  const channelShares = read_record(channelIntelligence.channel_shares);
  const deviceIntelligence = read_record(sourceSnapshot.device_intelligence);
  const companyGlobalProfile = read_record(sourceSnapshot.company_global_profile);
  const globalChannelShares = read_record(companyGlobalProfile.channel_shares);
  const globalChannelStrengths = read_record(companyGlobalProfile.channel_strengths);
  const globalDeviceProfile = read_record(companyGlobalProfile.device_profile);
  const globalTrafficQuality = read_record(companyGlobalProfile.traffic_quality);
  const showEvidenceLayers = report.strategy_mode === 'market_entry';
  return (
    <div className="space-y-5">
      {warnings.length ? <div className="rounded-md border border-amber-500/40 bg-amber-500/5 p-4"><p className="text-sm font-medium text-foreground">Fallback notes</p><ValueList items={warnings} /></div> : null}
      {marketEntryNoData ? <div className="rounded-md border border-sky-500/40 bg-sky-500/5 p-4"><p className="text-sm font-medium text-foreground">Market Entry context</p><p className="mt-2 text-sm text-muted-foreground">The selected company has no existing traffic in this country. This report uses market, competitor, and global company profile context.</p></div> : null}
      {deviceNote ? <div className="rounded-md border border-sky-500/40 bg-sky-500/5 p-4"><p className="text-sm font-medium text-foreground">Device context</p><p className="mt-2 text-sm text-muted-foreground">{deviceNote}</p></div> : null}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
        {[
          ['Strategy Mode', format_label(report.strategy_mode)],
          ['Country', `${report.country} (${report.country_code})`],
          ['Period', `${report.date_from} - ${report.date_to}`],
          ['Budget', `${amountFormatter.format(report.budget_amount)} ${report.currency}`],
          ['Scope', format_label(report.scope)],
          ['Opportunity Score', format_opportunity_score(report)],
          ['Generated', new Date(report.created_at).toLocaleString()],
        ].map(([label, value]) => <div className="rounded-md border bg-background p-4" key={label}><p className="text-xs text-muted-foreground">{label}</p><p className="mt-2 text-sm font-semibold text-foreground">{value}</p></div>)}
      </div>

      <div className="rounded-md border bg-background p-4">
        <div className="flex items-center gap-2"><h3 className="text-sm font-semibold">Marketing Recommendation</h3><InformationPopover ariaLabel="About the recommendation" title="Recommendation limitation">Directional, rule-based guidance from traffic and quality signals. It does not predict ROI, CPA, revenue, conversions, or customer counts.</InformationPopover></div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">{report.recommended_approach}</p>
      </div>

      {showEvidenceLayers ? <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-md border bg-background p-4">
          <h3 className="text-sm font-semibold">Target Market Channels</h3>
          <div className="mt-3 grid gap-2">
            <MetricRow label="Source" value={format_value(channelIntelligence.source)} />
            <MetricRow label="Dominant channel" value={format_value(channelIntelligence.dominant_channel)} />
            {channels.map((channel) => <MetricRow key={channel} label={format_label(channel)} value={format_share(channelShares[channel])} />)}
          </div>
        </div>
        <div className="rounded-md border bg-background p-4">
          <h3 className="text-sm font-semibold">Target Market Devices</h3>
          <div className="mt-3 grid gap-2">
            <MetricRow label="Source" value={format_value(deviceIntelligence.source)} />
            <MetricRow label="Dominant device" value={format_value(deviceIntelligence.dominant_device)} />
            <MetricRow label="Desktop share" value={format_share(deviceIntelligence.desktop_share)} />
            <MetricRow label="Mobile share" value={format_share(deviceIntelligence.mobile_share)} />
            <MetricRow label="Desktop quality" value={format_value(deviceIntelligence.desktop_quality_index)} />
            <MetricRow label="Mobile quality" value={format_value(deviceIntelligence.mobile_quality_index)} />
          </div>
        </div>
        <div className="rounded-md border bg-background p-4">
          <h3 className="text-sm font-semibold">Company Global Profile</h3>
          <div className="mt-3 grid gap-2">
            <MetricRow label="Available" value={companyGlobalProfile.available === true ? 'Yes' : 'No'} />
            <MetricRow label="Dominant channel" value={format_value(companyGlobalProfile.dominant_channel)} />
            {channels.map((channel) => <MetricRow key={channel} label={format_label(channel)} value={`${format_share(globalChannelShares[channel])} / ${format_value(globalChannelStrengths[channel])}`} />)}
            <MetricRow label="Global desktop" value={format_share(globalDeviceProfile.desktop_share)} />
            <MetricRow label="Global mobile" value={format_share(globalDeviceProfile.mobile_share)} />
            <MetricRow label="Global bounce" value={format_share(globalTrafficQuality.bounce_rate)} />
            <MetricRow label="Global duration" value={format_value(globalTrafficQuality.avg_visit_duration)} />
          </div>
        </div>
      </div> : null}

      <div className="rounded-md border bg-background p-4">
        <h3 className="text-sm font-semibold">Dependency Status</h3>
        <div className="mt-3 grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
          <p>Signals: <span className="font-medium text-foreground">{format_label(report.dependency_status.signals.status)}</span></p>
          <p>Opportunity Score: <span className="font-medium text-foreground">{format_label(report.dependency_status.opportunity_score.status)}</span></p>
        </div>
        {report.dependency_status.opportunity_score.message ? <p className="mt-3 text-xs text-muted-foreground">{report.dependency_status.opportunity_score.message}</p> : null}
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
