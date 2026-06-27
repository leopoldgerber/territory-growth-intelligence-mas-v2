'use client';

import { useEffect, useState, type FormEvent } from 'react';

import { MultiSelectFilter } from '@/components/dashboard/multi-select-filter';
import { Button } from '@/components/ui/button';
import { useBudgetFilterOptionsQuery } from '@/lib/api/report-queries';
import { filterDomainOptions, sanitizeFilterSelection } from '@/lib/dashboard/filter-options';
import type { BudgetStrategyGenerateRequest, StrategyMode } from '@/lib/types/reports';


const fieldClass = 'h-9 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:border-ring focus:ring-2 focus:ring-ring/40';
const modeCopy: Record<StrategyMode, string> = {
  existing_presence: 'Use this when the selected company already has traffic in the target country. The report optimizes current presence using company, market, and competitor data.',
  market_entry: 'Use this when the company may not yet have traffic in the target country. The report uses target-country market data, local competitors, and the company profile from other countries.',
};

export function BudgetStrategyForm({
  isPending,
  onSubmit,
}: {
  isPending: boolean;
  onSubmit: (request: BudgetStrategyGenerateRequest) => void;
}) {
  const [form, setForm] = useState<BudgetStrategyGenerateRequest>({
    strategy_mode: 'existing_presence',
    auto_prepare_dependencies: true,
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
  const allProjectOptionsQuery = useBudgetFilterOptionsQuery({
    ...form,
    country: 'all',
    tld: 'all',
    company: 'all',
    company_domain: 'all',
    competitors: 'all',
    competitor_domain: 'all',
  });
  const marketCompetitorOptionsQuery = useBudgetFilterOptionsQuery({
    ...form,
    company: 'all',
    company_domain: 'all',
    competitors: 'all',
    competitor_domain: 'all',
  });
  const isMarketEntry = form.strategy_mode === 'market_entry';
  const countrySource = isMarketEntry
    ? allProjectOptionsQuery.data
    : filterOptionsQuery.data;
  const companySource = isMarketEntry
    ? allProjectOptionsQuery.data
    : filterOptionsQuery.data;
  const competitorSource = isMarketEntry
    ? marketCompetitorOptionsQuery.data
    : filterOptionsQuery.data;
  const tldSource = isMarketEntry
    ? allProjectOptionsQuery.data
    : filterOptionsQuery.data;
  const countries = countrySource?.countries ?? [];
  const tlds = tldSource?.tlds ?? [];
  const companies = companySource?.companies ?? [];
  const domains = companySource?.domains ?? [];
  const competitorCompanies = competitorSource?.companies ?? [];
  const competitorDomainsSource = competitorSource?.domains ?? [];
  const companyDomains = filterDomainOptions(domains, form.company, form.tld);
  const competitorDomains = filterDomainOptions(competitorDomainsSource, form.competitors, form.tld);
  const marketEntryCompanySelected = (form.company !== 'all' && form.company !== 'none') || form.company_domain !== 'all';
  const countryFiltersLoading = isMarketEntry ? allProjectOptionsQuery.isLoading : filterOptionsQuery.isLoading;
  const companyFiltersLoading = isMarketEntry ? allProjectOptionsQuery.isLoading : filterOptionsQuery.isLoading;
  const competitorFiltersLoading = isMarketEntry ? marketCompetitorOptionsQuery.isLoading : filterOptionsQuery.isLoading;
  const submitDisabled = isPending
    || !form.country
    || countryFiltersLoading
    || competitorFiltersLoading
    || (isMarketEntry && (companyFiltersLoading || !marketEntryCompanySelected));

  useEffect(() => {
    if ((!isMarketEntry && !filterOptionsQuery.data) || !countrySource || !companySource || !competitorSource || !tldSource) {
      return;
    }
    setForm((current) => {
      const tld = sanitizeFilterSelection(current.tld, tldSource.tlds);
      const company = sanitizeFilterSelection(current.company, companySource.companies, true);
      const competitors = sanitizeFilterSelection(current.competitors, competitorSource.companies, true);
      const availableCompanyDomains = filterDomainOptions(companySource.domains, company, tld);
      const availableCompetitorDomains = filterDomainOptions(competitorSource.domains, competitors, tld);
      const companyDomain = sanitizeFilterSelection(current.company_domain, availableCompanyDomains);
      const competitorDomain = sanitizeFilterSelection(current.competitor_domain, availableCompetitorDomains);
      const countryAvailable = !current.country
        || countrySource.countries.some((option) => option.value === current.country);
      const country = countryAvailable || countrySource.countries.length === 0 ? current.country : '';
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
  }, [companySource, competitorSource, countrySource, filterOptionsQuery.data, isMarketEntry, tldSource]);

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
      const availableDomains = filterDomainOptions(
        domainKey === 'company_domain' ? domains : competitorDomainsSource,
        value,
        current.tld,
      );
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
        filterDomainOptions(competitorDomainsSource, current.competitors, value),
      ),
    }));
  }

  function submit_form(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <form className="space-y-4 border-b pb-5" onSubmit={submit_form}>
      <div className="grid gap-2 rounded-md border bg-background p-4">
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Strategy Mode
          <select
            className={fieldClass}
            onChange={(event) => update_field('strategy_mode', event.target.value as StrategyMode)}
            value={form.strategy_mode}
          >
            <option value="existing_presence">Existing Presence</option>
            <option value="market_entry">Market Entry</option>
          </select>
        </label>
        <p className="text-xs leading-5 text-muted-foreground">{modeCopy[form.strategy_mode]}</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <MultiSelectFilter
          allowAll={false}
          disabled={countryFiltersLoading}
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
          disabled={companyFiltersLoading}
          label="Company"
          onChange={(value) => update_company('company', 'company_domain', value)}
          options={companies}
          value={form.company}
        />
        <MultiSelectFilter
          disabled={companyFiltersLoading}
          label="Company Domain"
          onChange={(value) => update_field('company_domain', value)}
          options={companyDomains}
          value={form.company_domain}
        />
        <MultiSelectFilter
          allowNone
          disabled={competitorFiltersLoading}
          label="Competitors"
          onChange={(value) => update_company('competitors', 'competitor_domain', value)}
          options={competitorCompanies}
          value={form.competitors}
        />
        <MultiSelectFilter
          disabled={competitorFiltersLoading}
          label="Competitors Domain"
          onChange={(value) => update_field('competitor_domain', value)}
          options={competitorDomains}
          value={form.competitor_domain}
        />
        <MultiSelectFilter
          disabled={countryFiltersLoading}
          label="TLD"
          onChange={update_tld}
          options={tlds}
          value={form.tld}
        />
      </div>
      {filterOptionsQuery.isError ? (
        <p className="text-sm text-destructive">Failed to load available report filter values.</p>
      ) : null}
      {isPending ? (
        <div className="rounded-md border bg-secondary/40 p-3 text-xs leading-5 text-muted-foreground">
          Preparing analytics, recalculating signals if needed, recalculating opportunity score if needed, and generating budget strategy.
        </div>
      ) : null}
      <Button disabled={submitDisabled} type="submit">
        {isPending ? 'Preparing analytics...' : 'Generate budget strategy'}
      </Button>
    </form>
  );
}
