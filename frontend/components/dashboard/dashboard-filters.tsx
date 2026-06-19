'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo } from 'react';

import { MultiSelectFilter } from '@/components/dashboard/multi-select-filter';
import { Button } from '@/components/ui/button';
import { useAnalyticsFilterOptionsQuery } from '@/lib/api/analytics-queries';
import {
  buildDashboardHref,
  type DashboardFilterKey,
  type DashboardFilters,
  defaultDashboardFilters,
  ensureDashboardParams,
  readDashboardFilters,
  readDashboardValues,
  updateDashboardParams,
  writeDashboardValues,
} from '@/lib/dashboard/query-params';
import type { DomainFilterOption, FilterOption } from '@/lib/types/analytics';

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

const datePattern = /^\d{4}-\d{2}-\d{2}$/;

function filterDomains(domains: DomainFilterOption[], companyValue: string, tldValue: string): DomainFilterOption[] {
  if (companyValue === 'none') {
    return [];
  }
  const companyIds = new Set(readDashboardValues(companyValue).map(Number));
  const tlds = new Set(readDashboardValues(tldValue));
  return domains.filter((domain) => {
    const matchesCompany = companyIds.size === 0 || companyIds.has(domain.company_id);
    const matchesTld = tlds.size === 0 || (domain.tld !== null && tlds.has(domain.tld));
    return matchesCompany && matchesTld;
  });
}

function sanitizeSelection(value: string, options: FilterOption[], allowNone = false): string {
  if (value === 'none') {
    return allowNone ? 'none' : 'all';
  }
  const selectedValues = readDashboardValues(value);
  if (selectedValues.length === 0) {
    return 'all';
  }
  const optionValues = new Set(options.map((option) => option.value));
  return writeDashboardValues(selectedValues.filter((item) => optionValues.has(item)));
}

export function DashboardFilters() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchText = searchParams.toString();
  const currentParams = useMemo(() => new URLSearchParams(searchText), [searchText]);
  const filters = readDashboardFilters(currentParams);
  const filterOptionsQuery = useAnalyticsFilterOptionsQuery();
  const countries = filterOptionsQuery.data?.countries ?? [];
  const tlds = filterOptionsQuery.data?.tlds ?? [];
  const companies = filterOptionsQuery.data?.companies ?? [];
  const domains = filterOptionsQuery.data?.domains ?? [];
  const companyDomains = filterDomains(domains, filters.company, filters.tld);
  const competitorDomains = filterDomains(domains, filters.competitors, filters.tld);

  useEffect(() => {
    const previousParams = new URLSearchParams(searchText);
    const nextParams = ensureDashboardParams(previousParams);
    const nextHref = buildDashboardHref(pathname, nextParams);
    const currentHref = buildDashboardHref(pathname, previousParams);

    if (nextHref !== currentHref) {
      router.replace(nextHref, { scroll: false });
    }
  }, [pathname, router, searchText]);

  useEffect(() => {
    if (!filterOptionsQuery.data) {
      return;
    }

    const updates: Partial<DashboardFilters> = {};
    const countryValue = sanitizeSelection(filters.country, filterOptionsQuery.data.countries);
    const tldValue = sanitizeSelection(filters.tld, filterOptionsQuery.data.tlds);
    const companyValue = sanitizeSelection(filters.company, filterOptionsQuery.data.companies, true);
    const competitorsValue = sanitizeSelection(filters.competitors, filterOptionsQuery.data.companies, true);
    const availableCompanyDomains = filterDomains(filterOptionsQuery.data.domains, companyValue, tldValue);
    const availableCompetitorDomains = filterDomains(filterOptionsQuery.data.domains, competitorsValue, tldValue);
    const companyDomainValue = sanitizeSelection(filters.companyDomain, availableCompanyDomains);
    const competitorDomainValue = sanitizeSelection(filters.competitorDomain, availableCompetitorDomains);

    if (countryValue !== filters.country) {
      updates.country = countryValue;
    }
    if (tldValue !== filters.tld) {
      updates.tld = tldValue;
    }
    if (companyValue !== filters.company) {
      updates.company = companyValue;
    }
    if (companyDomainValue !== filters.companyDomain) {
      updates.companyDomain = companyDomainValue;
    }
    if (competitorsValue !== filters.competitors) {
      updates.competitors = competitorsValue;
    }
    if (competitorDomainValue !== filters.competitorDomain) {
      updates.competitorDomain = competitorDomainValue;
    }
    if (Object.keys(updates).length === 0) {
      return;
    }

    const nextParams = updateDashboardParams(currentParams, updates);
    const nextHref = buildDashboardHref(pathname, nextParams);
    router.replace(nextHref, { scroll: false });
  }, [
    currentParams,
    filterOptionsQuery.data,
    filters.company,
    filters.companyDomain,
    filters.competitorDomain,
    filters.competitors,
    filters.country,
    filters.tld,
    pathname,
    router,
  ]);

  function updateFilter(key: DashboardFilterKey, value: string): void {
    const nextParams = updateDashboardParams(currentParams, { [key]: value } as Partial<DashboardFilters>);
    const nextHref = buildDashboardHref(pathname, nextParams);

    router.replace(nextHref, { scroll: false });
  }

  function updateFilters(updates: Partial<DashboardFilters>): void {
    const nextParams = updateDashboardParams(currentParams, updates);
    const nextHref = buildDashboardHref(pathname, nextParams);

    router.replace(nextHref, { scroll: false });
  }

  function updateCompanyFilter(
    companyKey: Extract<DashboardFilterKey, 'company' | 'competitors'>,
    domainKey: Extract<DashboardFilterKey, 'companyDomain' | 'competitorDomain'>,
    value: string,
  ): void {
    const availableDomains = filterDomains(domains, value, filters.tld);
    const domainValue = sanitizeSelection(filters[domainKey], availableDomains);
    updateFilters({ [companyKey]: value, [domainKey]: domainValue });
  }

  function updateTldFilter(value: string): void {
    const availableCompanyDomains = filterDomains(domains, filters.company, value);
    const availableCompetitorDomains = filterDomains(domains, filters.competitors, value);
    updateFilters({
      tld: value,
      companyDomain: sanitizeSelection(filters.companyDomain, availableCompanyDomains),
      competitorDomain: sanitizeSelection(filters.competitorDomain, availableCompetitorDomains),
    });
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
      tld: defaultDashboardFilters.tld,
      company: defaultDashboardFilters.company,
      companyDomain: defaultDashboardFilters.companyDomain,
      competitors: defaultDashboardFilters.competitors,
      competitorDomain: defaultDashboardFilters.competitorDomain,
    });
    const nextHref = buildDashboardHref(pathname, nextParams);

    router.replace(nextHref, { scroll: false });
  }

  return (
    <section className="border-y bg-card/30">
      <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-4">
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
        <MultiSelectFilter
          disabled={filterOptionsQuery.isLoading}
          label="Country"
          onChange={(value) => updateFilter('country', value)}
          options={countries}
          value={filters.country}
        />
        <MultiSelectFilter
          disabled={filterOptionsQuery.isLoading}
          label="Top-Level Domain"
          onChange={updateTldFilter}
          options={tlds}
          value={filters.tld}
        />
        <MultiSelectFilter
          allowNone
          disabled={filterOptionsQuery.isLoading}
          label="Company"
          onChange={(value) => updateCompanyFilter('company', 'companyDomain', value)}
          options={companies}
          value={filters.company}
        />
        <MultiSelectFilter
          disabled={filterOptionsQuery.isLoading}
          label="Company Domain"
          onChange={(value) => updateFilter('companyDomain', value)}
          options={companyDomains}
          value={filters.companyDomain}
        />
        <MultiSelectFilter
          allowNone
          disabled={filterOptionsQuery.isLoading}
          label="Competitors"
          onChange={(value) => updateCompanyFilter('competitors', 'competitorDomain', value)}
          options={companies}
          value={filters.competitors}
        />
        <MultiSelectFilter
          disabled={filterOptionsQuery.isLoading}
          label="Competitors Domain"
          onChange={(value) => updateFilter('competitorDomain', value)}
          options={competitorDomains}
          value={filters.competitorDomain}
        />
        <div className="flex items-end">
          <Button className="w-full xl:w-auto" onClick={clearFilters} type="button" variant="outline">
            Clear
          </Button>
        </div>
      </div>
    </section>
  );
}
