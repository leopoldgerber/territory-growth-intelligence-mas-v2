'use client';

import { useEffect, useState, type FormEvent } from 'react';

import { MultiSelectFilter } from '@/components/dashboard/multi-select-filter';
import { Button } from '@/components/ui/button';
import { useBudgetFilterOptionsQuery } from '@/lib/api/report-queries';
import { filterDomainOptions, sanitizeFilterSelection } from '@/lib/dashboard/filter-options';
import type { BudgetStrategyGenerateRequest } from '@/lib/types/reports';


const fieldClass = 'h-9 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:border-ring focus:ring-2 focus:ring-ring/40';

export function BudgetStrategyForm({
  isPending,
  onSubmit,
}: {
  isPending: boolean;
  onSubmit: (request: BudgetStrategyGenerateRequest) => void;
}) {
  const [form, setForm] = useState<BudgetStrategyGenerateRequest>({
    date_from: '2025-01-01',
    date_to: '2025-02-01',
    country: '',
    budget_amount: 10000,
    currency: 'USD',
    company: 'all',
    company_domain: 'all',
    competitors: 'all',
    competitor_domain: 'all',
    tld: 'all',
    calculation_version: 'v1',
  });
  const filterOptionsQuery = useBudgetFilterOptionsQuery(form);
  const countries = filterOptionsQuery.data?.countries ?? [];
  const tlds = filterOptionsQuery.data?.tlds ?? [];
  const companies = filterOptionsQuery.data?.companies ?? [];
  const domains = filterOptionsQuery.data?.domains ?? [];
  const companyDomains = filterDomainOptions(domains, form.company, form.tld);
  const competitorDomains = filterDomainOptions(domains, form.competitors, form.tld);

  useEffect(() => {
    if (!filterOptionsQuery.data) {
      return;
    }
    setForm((current) => {
      const tld = sanitizeFilterSelection(current.tld, filterOptionsQuery.data.tlds);
      const company = sanitizeFilterSelection(current.company, filterOptionsQuery.data.companies, true);
      const competitors = sanitizeFilterSelection(current.competitors, filterOptionsQuery.data.companies, true);
      const availableCompanyDomains = filterDomainOptions(filterOptionsQuery.data.domains, company, tld);
      const availableCompetitorDomains = filterDomainOptions(filterOptionsQuery.data.domains, competitors, tld);
      const companyDomain = sanitizeFilterSelection(current.company_domain, availableCompanyDomains);
      const competitorDomain = sanitizeFilterSelection(current.competitor_domain, availableCompetitorDomains);
      const countryAvailable = !current.country
        || filterOptionsQuery.data.countries.some((option) => option.value === current.country);
      const country = countryAvailable || filterOptionsQuery.data.countries.length === 0 ? current.country : '';
      if (
        country === current.country
        && tld === current.tld
        && company === current.company
        && companyDomain === current.company_domain
        && competitors === current.competitors
        && competitorDomain === current.competitor_domain
      ) {
        return current;
      }
      return {
        ...current,
        country,
        tld,
        company,
        company_domain: companyDomain,
        competitors,
        competitor_domain: competitorDomain,
      };
    });
  }, [filterOptionsQuery.data]);

  function update_field<Key extends keyof BudgetStrategyGenerateRequest>(
    key: Key,
    value: BudgetStrategyGenerateRequest[Key],
  ): void {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function update_company(
    companyKey: 'company' | 'competitors',
    domainKey: 'company_domain' | 'competitor_domain',
    value: string,
  ): void {
    setForm((current) => {
      const availableDomains = filterDomainOptions(domains, value, current.tld);
      return {
        ...current,
        [companyKey]: value,
        [domainKey]: sanitizeFilterSelection(current[domainKey], availableDomains),
      };
    });
  }

  function update_tld(value: string): void {
    setForm((current) => ({
      ...current,
      tld: value,
      company_domain: sanitizeFilterSelection(
        current.company_domain,
        filterDomainOptions(domains, current.company, value),
      ),
      competitor_domain: sanitizeFilterSelection(
        current.competitor_domain,
        filterDomainOptions(domains, current.competitors, value),
      ),
    }));
  }

  function submit_form(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <form className="space-y-4 border-b pb-5" onSubmit={submit_form}>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <MultiSelectFilter
          allowAll={false}
          disabled={filterOptionsQuery.isLoading}
          label="Country"
          onChange={(value) => update_field('country', value)}
          options={countries}
          placeholder="Select country"
          single
          value={form.country}
        />
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Date from
          <input className={fieldClass} onChange={(event) => update_field('date_from', event.target.value)} required type="date" value={form.date_from} />
        </label>
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Date to
          <input className={fieldClass} onChange={(event) => update_field('date_to', event.target.value)} required type="date" value={form.date_to} />
        </label>
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Budget amount
          <input className={fieldClass} min="0.01" onChange={(event) => update_field('budget_amount', Number(event.target.value))} required step="0.01" type="number" value={form.budget_amount} />
        </label>
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Currency
          <select className={fieldClass} onChange={(event) => update_field('currency', event.target.value as 'USD' | 'EUR')} value={form.currency}>
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
          </select>
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <MultiSelectFilter
          allowNone
          disabled={filterOptionsQuery.isLoading}
          label="Company"
          onChange={(value) => update_company('company', 'company_domain', value)}
          options={companies}
          value={form.company}
        />
        <MultiSelectFilter
          disabled={filterOptionsQuery.isLoading}
          label="Company Domain"
          onChange={(value) => update_field('company_domain', value)}
          options={companyDomains}
          value={form.company_domain}
        />
        <MultiSelectFilter
          allowNone
          disabled={filterOptionsQuery.isLoading}
          label="Competitors"
          onChange={(value) => update_company('competitors', 'competitor_domain', value)}
          options={companies}
          value={form.competitors}
        />
        <MultiSelectFilter
          disabled={filterOptionsQuery.isLoading}
          label="Competitors Domain"
          onChange={(value) => update_field('competitor_domain', value)}
          options={competitorDomains}
          value={form.competitor_domain}
        />
        <MultiSelectFilter
          disabled={filterOptionsQuery.isLoading}
          label="TLD"
          onChange={update_tld}
          options={tlds}
          value={form.tld}
        />
      </div>
      {filterOptionsQuery.isError ? (
        <p className="text-sm text-destructive">Failed to load available report filter values.</p>
      ) : null}
      <Button disabled={isPending || !form.country || filterOptionsQuery.isLoading} type="submit">
        {isPending ? 'Generating strategy...' : 'Generate budget strategy'}
      </Button>
    </form>
  );
}
