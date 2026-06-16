'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect } from 'react';

import { Button } from '@/components/ui/button';
import {
  buildDashboardHref,
  type DashboardFilterKey,
  type DashboardFilters,
  defaultDashboardFilters,
  ensureDashboardParams,
  readDashboardFilters,
  updateDashboardParams,
} from '@/lib/dashboard/query-params';

const filterFields: {
  key: DashboardFilterKey;
  label: string;
  type: string;
}[] = [
  {
    key: 'dateFrom',
    label: 'Date from',
    type: 'date',
  },
  {
    key: 'dateTo',
    label: 'Date to',
    type: 'date',
  },
];

const selectFields: {
  key: Extract<DashboardFilterKey, 'country' | 'domain'>;
  label: string;
  options: { label: string; value: string }[];
}[] = [
  {
    key: 'country',
    label: 'Country',
    options: [{ label: 'All', value: 'all' }],
  },
  {
    key: 'domain',
    label: 'Competitor / Domain',
    options: [{ label: 'All', value: 'all' }],
  },
];

const datePattern = /^\d{4}-\d{2}-\d{2}$/;

export function DashboardFilters() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchText = searchParams.toString();
  const currentParams = new URLSearchParams(searchText);
  const filters = readDashboardFilters(currentParams);

  useEffect(() => {
    const previousParams = new URLSearchParams(searchText);
    const nextParams = ensureDashboardParams(previousParams);
    const nextHref = buildDashboardHref(pathname, nextParams);
    const currentHref = buildDashboardHref(pathname, previousParams);

    if (nextHref !== currentHref) {
      router.replace(nextHref, { scroll: false });
    }
  }, [pathname, router, searchText]);

  function updateFilter(key: DashboardFilterKey, value: string): void {
    const nextParams = updateDashboardParams(currentParams, { [key]: value } as Partial<DashboardFilters>);
    const nextHref = buildDashboardHref(pathname, nextParams);

    router.replace(nextHref, { scroll: false });
  }

  function updateDate(key: DashboardFilterKey, value: string): void {
    if (!datePattern.test(value)) {
      return;
    }

    updateFilter(key, value);
  }

  function resetDate(key: DashboardFilterKey, value: string): void {
    if (datePattern.test(value)) {
      return;
    }

    updateFilter(key, defaultDashboardFilters[key]);
  }

  function clearFilters(): void {
    const nextParams = updateDashboardParams(currentParams, {
      dateFrom: defaultDashboardFilters.dateFrom,
      dateTo: defaultDashboardFilters.dateTo,
      country: defaultDashboardFilters.country,
      domain: defaultDashboardFilters.domain,
    });
    const nextHref = buildDashboardHref(pathname, nextParams);

    router.replace(nextHref, { scroll: false });
  }

  return (
    <section className="border-y bg-card/30">
      <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-[repeat(4,minmax(0,1fr))_auto]">
        {filterFields.map((field) => (
          <label key={field.key} className="grid gap-1.5 text-xs font-medium text-muted-foreground">
            <span>{field.label}</span>
            <input
              key={`${field.key}-${filters[field.key]}`}
              className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-2 focus:ring-ring/40"
              defaultValue={filters[field.key]}
              onBlur={(event) => resetDate(field.key, event.target.value)}
              onChange={(event) => updateDate(field.key, event.target.value)}
              type={field.type}
            />
          </label>
        ))}
        {selectFields.map((field) => (
          <label key={field.key} className="grid gap-1.5 text-xs font-medium text-muted-foreground">
            <span>{field.label}</span>
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-2 focus:ring-ring/40"
              onChange={(event) => updateFilter(field.key, event.target.value)}
              value={filters[field.key]}
            >
              {field.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        ))}
        <div className="flex items-end">
          <Button className="w-full xl:w-auto" onClick={clearFilters} type="button" variant="outline">
            Clear
          </Button>
        </div>
      </div>
    </section>
  );
}
