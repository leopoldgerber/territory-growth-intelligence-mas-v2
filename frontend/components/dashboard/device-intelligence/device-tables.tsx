import { Badge } from '@/components/ui/badge';
import type { CompetitorDeviceQuality, DeviceTrendPoint } from '@/lib/types/analytics';

import { DeviceComparisonValue, type DeviceComparisonProps } from './device-comparison';


const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});
const numberFormatter = new Intl.NumberFormat('en-US');

function format_duration(seconds: number): string {
  const absoluteSeconds = Math.round(Math.abs(seconds));
  const minutes = Math.floor(absoluteSeconds / 60);
  const remainingSeconds = absoluteSeconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function format_label(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());
}

export function DeviceTrendTable({ combinedScopes, companyScope, competitorScope }: DeviceComparisonProps) {
  const companyRows = new Map((companyScope?.device_trend ?? []).map((row) => [row.date, row]));
  const competitorRows = new Map((competitorScope?.device_trend ?? []).map((row) => [row.date, row]));
  const dates = Array.from(new Set([...companyRows.keys(), ...competitorRows.keys()])).sort();
  if (dates.length === 0) {
    return null;
  }

  function read_value(row: DeviceTrendPoint | undefined, field: keyof DeviceTrendPoint): string | null {
    if (!row) {
      return '0';
    }
    const value = row[field];
    return field.endsWith('_share') ? percentFormatter.format(value as number) : numberFormatter.format(value as number);
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Daily Device Trend</h3>
      <div className="max-h-96 overflow-auto rounded-md border bg-background">
        <table className="w-full min-w-[620px] text-sm">
          <thead className="sticky top-0 bg-secondary text-muted-foreground">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Date</th>
              <th className="px-3 py-2 text-right font-medium text-[#FB7185]">Desktop Visits</th>
              <th className="px-3 py-2 text-right font-medium text-[#FDBA74]">Mobile Visits</th>
              <th className="px-3 py-2 text-right font-medium text-[#FB7185]">Desktop Share</th>
              <th className="px-3 py-2 text-right font-medium text-[#FDBA74]">Mobile Share</th>
            </tr>
          </thead>
          <tbody>
            {dates.map((date) => {
              const companyRow = companyRows.get(date);
              const competitorRow = competitorRows.get(date);
              return (
                <tr className="border-t" key={date}>
                  <td className="px-3 py-2 font-medium text-foreground">{date}</td>
                  {(['desktop_visits', 'mobile_visits', 'desktop_share', 'mobile_share'] as const).map((field) => (
                    <td className="px-3 py-2 text-right" key={field}>
                      <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={read_value(companyRow, field)} competitorValue={competitorScope ? read_value(competitorRow, field) : null} />
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function CompetitorDeviceTable({ combinedScopes, companyScope, competitorScope }: DeviceComparisonProps) {
  const rows: Array<{ row: CompetitorDeviceQuality; tone: 'neutral' | 'company' | 'competitor' }> = [
    ...(companyScope?.competitor_device_quality ?? []).map((row) => ({ row, tone: combinedScopes ? 'neutral' as const : 'company' as const })),
    ...(competitorScope?.competitor_device_quality ?? []).map((row) => ({ row, tone: 'competitor' as const })),
  ];
  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Company Device Quality</h3>
      <div className="overflow-x-auto rounded-md border bg-background">
        <table className="w-full min-w-[1040px] text-sm">
          <thead className="bg-secondary text-muted-foreground">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Company</th>
              <th className="px-3 py-2 text-right font-medium text-[#FB7185]">Desktop Share</th>
              <th className="px-3 py-2 text-right font-medium text-[#FDBA74]">Mobile Share</th>
              <th className="px-3 py-2 text-right font-medium text-[#FB7185]">Desktop Bounce</th>
              <th className="px-3 py-2 text-right font-medium text-[#FDBA74]">Mobile Bounce</th>
              <th className="px-3 py-2 text-right font-medium text-[#FB7185]">Desktop Duration</th>
              <th className="px-3 py-2 text-right font-medium text-[#FDBA74]">Mobile Duration</th>
              <th className="px-3 py-2 text-right font-medium">Quality Gap</th>
              <th className="px-3 py-2 text-right font-medium">Signal</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ row, tone }, index) => {
              const valueClass = tone === 'company' ? 'text-emerald-500' : tone === 'competitor' ? 'text-sky-500' : 'text-foreground';
              return (
                <tr className={`border-t ${valueClass}`} key={`${tone}-${row.company_id}-${index}`}>
                  <td className="px-3 py-2 font-medium">{row.company}</td>
                  <td className="px-3 py-2 text-right">{percentFormatter.format(row.desktop_share)}</td>
                  <td className="px-3 py-2 text-right">{percentFormatter.format(row.mobile_share)}</td>
                  <td className="px-3 py-2 text-right">{percentFormatter.format(row.desktop_bounce_rate)}</td>
                  <td className="px-3 py-2 text-right">{percentFormatter.format(row.mobile_bounce_rate)}</td>
                  <td className="px-3 py-2 text-right">{format_duration(row.desktop_duration)}</td>
                  <td className="px-3 py-2 text-right">{format_duration(row.mobile_duration)}</td>
                  <td className="px-3 py-2 text-right">{percentFormatter.format(row.quality_gap)}</td>
                  <td className="px-3 py-2 text-right"><Badge className="ml-auto w-fit" variant="outline">{format_label(row.signal)}</Badge></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
