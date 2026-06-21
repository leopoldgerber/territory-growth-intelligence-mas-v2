import { InformationPopover } from '@/components/dashboard/information-popover';

import { DeviceComparisonValue, type DeviceComparisonProps } from './device-comparison';


const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
  style: 'percent',
});

function format_duration(seconds: number): string {
  const sign = seconds < 0 ? '-' : '';
  const absoluteSeconds = Math.round(Math.abs(seconds));
  const minutes = Math.floor(absoluteSeconds / 60);
  const remainingSeconds = absoluteSeconds % 60;
  return `${sign}${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function DeviceLabel({ device, label }: { device?: 'desktop' | 'mobile'; label: string }) {
  const deviceClass = device === 'desktop' ? 'bg-[#FB7185]' : device === 'mobile' ? 'bg-[#FDBA74]' : '';
  return (
    <span className="flex items-center gap-1.5 text-muted-foreground">
      {deviceClass ? <span className={`h-2 w-2 rounded-sm ${deviceClass}`} /> : null}
      {label}
    </span>
  );
}

function ScopeSplit({
  label,
  labelClass,
  desktopShare,
  mobileShare,
}: {
  label: string;
  labelClass: string;
  desktopShare: number;
  mobileShare: number;
}) {
  return (
    <div className="grid gap-1.5">
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className={`font-medium ${labelClass}`}>{label}</span>
        <span className="text-muted-foreground">
          <span className="text-[#FB7185]">{percentFormatter.format(desktopShare)}</span>
          {' | '}
          <span className="text-[#FDBA74]">{percentFormatter.format(mobileShare)}</span>
        </span>
      </div>
      <div className="flex h-2 overflow-hidden rounded-sm bg-secondary">
        <div className="h-full bg-[#FB7185]" style={{ width: `${Math.min(desktopShare * 100, 100)}%` }} />
        <div className="h-full bg-[#FDBA74]" style={{ width: `${Math.min(mobileShare * 100, 100)}%` }} />
      </div>
    </div>
  );
}

export function DeviceMetricCards({ combinedScopes, companyScope, competitorScope }: DeviceComparisonProps) {
  const companySummary = companyScope?.summary;
  const competitorSummary = competitorScope?.summary;
  const companyQuality = companyScope?.quality;
  const competitorQuality = competitorScope?.quality;
  const companyBounce = companyScope?.bounce_split;
  const competitorBounce = competitorScope?.bounce_split;

  return (
    <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
      <div className="rounded-md border bg-background p-4">
        <h3 className="text-sm font-semibold text-foreground">Device Split</h3>
        <div className="mt-4 grid gap-4">
          {companySummary ? (
            <ScopeSplit
              desktopShare={companySummary.desktop_share}
              label={combinedScopes ? 'Overall' : 'Company'}
              labelClass={combinedScopes ? 'text-foreground' : 'text-emerald-500'}
              mobileShare={companySummary.mobile_share}
            />
          ) : null}
          {competitorSummary ? (
            <ScopeSplit
              desktopShare={competitorSummary.desktop_share}
              label="Competitors"
              labelClass="text-sky-500"
              mobileShare={competitorSummary.mobile_share}
            />
          ) : null}
        </div>
      </div>

      <div className="rounded-md border bg-background p-4">
        <h3 className="text-sm font-semibold text-foreground">Unique Users</h3>
        <div className="mt-4 grid gap-3 text-sm">
          {[
            ['All devices', undefined, 'unique_total'],
            ['Desktop', 'desktop', 'desktop_unique'],
            ['Mobile', 'mobile', 'mobile_unique'],
          ].map(([label, device, field]) => (
            <div className="flex justify-between gap-3" key={field}>
              <DeviceLabel device={device as 'desktop' | 'mobile' | undefined} label={label as string} />
              <DeviceComparisonValue
                combinedScopes={combinedScopes}
                companyValue={companySummary ? numberFormatter.format(companySummary[field as keyof typeof companySummary] as number) : null}
                competitorValue={competitorSummary ? numberFormatter.format(competitorSummary[field as keyof typeof competitorSummary] as number) : null}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-md border bg-background p-4">
        <h3 className="text-sm font-semibold text-foreground">Bounce / No-Bounce</h3>
        <div className="mt-4 grid gap-3 text-sm">
          <div className="flex justify-between gap-3">
            <DeviceLabel device="desktop" label="Desktop bounce" />
            <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={companyQuality ? percentFormatter.format(companyQuality.desktop_bounce_rate) : null} competitorValue={competitorQuality ? percentFormatter.format(competitorQuality.desktop_bounce_rate) : null} />
          </div>
          <div className="flex justify-between gap-3">
            <DeviceLabel device="mobile" label="Mobile bounce" />
            <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={companyQuality ? percentFormatter.format(companyQuality.mobile_bounce_rate) : null} competitorValue={competitorQuality ? percentFormatter.format(competitorQuality.mobile_bounce_rate) : null} />
          </div>
          <div className="flex justify-between gap-3">
            <DeviceLabel device="desktop" label="Desktop no-bounce" />
            <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={companyBounce ? numberFormatter.format(companyBounce.desktop_no_bounce) : null} competitorValue={competitorBounce ? numberFormatter.format(competitorBounce.desktop_no_bounce) : null} />
          </div>
          <div className="flex justify-between gap-3">
            <DeviceLabel device="mobile" label="Mobile no-bounce" />
            <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={companyBounce ? numberFormatter.format(companyBounce.mobile_no_bounce) : null} competitorValue={competitorBounce ? numberFormatter.format(competitorBounce.mobile_no_bounce) : null} />
          </div>
        </div>
      </div>

      <div className="rounded-md border bg-background p-4">
        <h3 className="text-sm font-semibold text-foreground">Duration Comparison</h3>
        <div className="mt-4 grid gap-3 text-sm">
          {[
            ['All devices', undefined, 'duration_total'],
            ['Desktop', 'desktop', 'desktop_duration'],
            ['Mobile', 'mobile', 'mobile_duration'],
            ['Desktop - mobile', undefined, 'duration_gap'],
          ].map(([label, device, field], index) => (
            <div className={`flex justify-between gap-3 ${index === 3 ? 'border-t pt-3' : ''}`} key={field}>
              <DeviceLabel device={device as 'desktop' | 'mobile' | undefined} label={label as string} />
              <DeviceComparisonValue
                combinedScopes={combinedScopes}
                companyValue={companyQuality ? format_duration(companyQuality[field as keyof typeof companyQuality] as number) : null}
                competitorValue={competitorQuality ? format_duration(competitorQuality[field as keyof typeof competitorQuality] as number) : null}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-md border bg-background p-4 lg:col-span-2 xl:col-span-2">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-foreground">Device Quality Comparison</h3>
          <InformationPopover ariaLabel="About device quality index" title="Device Quality Index">
            A comparative signal combining normalized visit duration and no-bounce rate with equal weights. It is not a final score or recommendation.
          </InformationPopover>
        </div>
        <div className="mt-4 grid gap-3 text-sm">
          <div className="flex justify-between gap-3">
            <DeviceLabel device="desktop" label="Desktop quality" />
            <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={companyQuality ? percentFormatter.format(companyQuality.desktop_quality_index) : null} competitorValue={competitorQuality ? percentFormatter.format(competitorQuality.desktop_quality_index) : null} />
          </div>
          <div className="flex justify-between gap-3">
            <DeviceLabel device="mobile" label="Mobile quality" />
            <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={companyQuality ? percentFormatter.format(companyQuality.mobile_quality_index) : null} competitorValue={competitorQuality ? percentFormatter.format(competitorQuality.mobile_quality_index) : null} />
          </div>
          <div className="flex justify-between gap-3 border-t pt-3">
            <span className="text-muted-foreground">Quality gap</span>
            <DeviceComparisonValue combinedScopes={combinedScopes} companyValue={companyQuality ? percentFormatter.format(companyQuality.quality_gap) : null} competitorValue={competitorQuality ? percentFormatter.format(competitorQuality.quality_gap) : null} />
          </div>
        </div>
      </div>
    </div>
  );
}
