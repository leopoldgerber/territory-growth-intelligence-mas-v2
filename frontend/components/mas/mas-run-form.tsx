'use client';

import { useQuery } from '@tanstack/react-query';
import { Play } from 'lucide-react';
import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { MultiSelectFilter } from '@/components/dashboard/multi-select-filter';
import { Button } from '@/components/ui/button';
import { getAnalyticsFilterOptions } from '@/lib/api/analytics';
import type { MasStrategyMode, MasWorkflowRequest } from '@/lib/types/mas';


const fieldClass = 'h-9 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:border-ring focus:ring-2 focus:ring-ring/40';

type MasFormState = {
  strategyMode: MasStrategyMode;
  country: string;
  company: string;
  dateFrom: string;
  dateTo: string;
  budgetAmount: number;
  currency: 'USD' | 'EUR';
  userQuery: string;
  useRag: boolean;
};

const modeCopy: Record<MasStrategyMode, string> = {
  market_entry: 'Target company and target country are independent. Competitors stay tied to the selected country.',
  existing_presence: 'Company should already have data in the selected country. Use it for optimization of current presence.',
};

export function MasRunForm({
  isPending,
  onSubmit,
}: {
  isPending: boolean;
  onSubmit: (request: MasWorkflowRequest) => void;
}) {
  const [form, setForm] = useState<MasFormState>({
    strategyMode: 'market_entry',
    country: '',
    company: 'none',
    dateFrom: '2025-01-01',
    dateTo: '2025-02-01',
    budgetAmount: 10000,
    currency: 'USD',
    userQuery: '',
    useRag: true,
  });
  const allOptionsQuery = useQuery({
    queryKey: ['mas', 'filter-options', 'all', form.dateFrom, form.dateTo],
    queryFn: () => getAnalyticsFilterOptions(baseFilters(form, 'all', 'all')),
  });
  const filteredOptionsQuery = useQuery({
    queryKey: ['mas', 'filter-options', form.dateFrom, form.dateTo, form.country, form.company],
    queryFn: () => getAnalyticsFilterOptions(baseFilters(form, form.country || 'all', form.company)),
  });
  const isMarketEntry = form.strategyMode === 'market_entry';
  const countrySource = isMarketEntry ? allOptionsQuery.data : filteredOptionsQuery.data;
  const companySource = isMarketEntry ? allOptionsQuery.data : filteredOptionsQuery.data;
  const countries = countrySource?.countries ?? [];
  const companies = companySource?.companies ?? [];
  const selectedCountry = countries.find((item) => item.value === form.country);
  const selectedCompany = companies.find((item) => item.value === form.company);
  const companyReady = Boolean(selectedCompany);
  const countryReady = Boolean(selectedCountry);
  const submitDisabled = isPending
    || allOptionsQuery.isLoading
    || filteredOptionsQuery.isLoading
    || !companyReady
    || !countryReady
    || form.budgetAmount <= 0;

  useEffect(() => {
    if (!countrySource || !companySource) {
      return;
    }
    setForm((current) => {
      const countryExists = !current.country || countrySource.countries.some((item) => item.value === current.country);
      const companyExists = current.company === 'none' || companySource.companies.some((item) => item.value === current.company);
      if (countryExists && companyExists) {
        return current;
      }
      return {
        ...current,
        country: countryExists ? current.country : '',
        company: companyExists ? current.company : 'none',
      };
    });
  }, [companySource, countrySource]);

  const previewQuery = useMemo(
    () => buildQuestion(form, selectedCountry?.label, selectedCompany?.label),
    [form, selectedCompany?.label, selectedCountry?.label],
  );

  function updateField<Key extends keyof MasFormState>(key: Key, value: MasFormState[Key]): void {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function submitForm(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!selectedCountry || !selectedCompany) {
      return;
    }
    onSubmit({
      project_id: null,
      user_query: form.userQuery.trim() || previewQuery,
      default_context: {
        strategy_mode: form.strategyMode,
        country: selectedCountry.label,
        company: selectedCompany.label,
        date_from: form.dateFrom,
        date_to: form.dateTo,
        budget_amount: form.budgetAmount,
        currency: form.currency,
      },
      options: {
        use_rag: form.useRag,
        save_result: true,
        run_mode: 'sync',
      },
    });
  }

  return (
    <form className="space-y-5" onSubmit={submitForm}>
      <div className="grid gap-3 lg:grid-cols-[1.1fr_1fr]">
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Project
          <input className={fieldClass} disabled readOnly value="Default project" />
        </label>
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Strategy Mode
          <select
            className={fieldClass}
            onChange={(event) => updateField('strategyMode', event.target.value as MasStrategyMode)}
            value={form.strategyMode}
          >
            <option value="market_entry">Market Entry</option>
            <option value="existing_presence">Existing Presence</option>
          </select>
        </label>
      </div>
      <p className="rounded-md border bg-secondary/30 px-3 py-2 text-xs leading-5 text-muted-foreground">
        {modeCopy[form.strategyMode]}
      </p>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MultiSelectFilter
          allowAll={false}
          disabled={allOptionsQuery.isLoading || filteredOptionsQuery.isLoading}
          label="Country"
          onChange={(value) => updateField('country', value)}
          options={countries}
          placeholder="Select country"
          single
          value={form.country}
        />
        <MultiSelectFilter
          allowAll={false}
          allowNone
          disabled={allOptionsQuery.isLoading || filteredOptionsQuery.isLoading}
          label="Company"
          onChange={(value) => updateField('company', value)}
          options={companies}
          placeholder="Select company"
          single
          value={form.company}
        />
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Date from
          <input
            className={fieldClass}
            onChange={(event) => updateField('dateFrom', event.target.value)}
            required
            type="date"
            value={form.dateFrom}
          />
        </label>
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Date to
          <input
            className={fieldClass}
            onChange={(event) => updateField('dateTo', event.target.value)}
            required
            type="date"
            value={form.dateTo}
          />
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-[1fr_160px_160px]">
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          User question
          <textarea
            className="min-h-24 w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-ring focus:ring-2 focus:ring-ring/40"
            onChange={(event) => updateField('userQuery', event.target.value)}
            placeholder={previewQuery}
            value={form.userQuery}
          />
        </label>
        <label className="grid content-start gap-1.5 text-xs font-medium text-muted-foreground">
          Budget amount
          <input
            className={fieldClass}
            min="0.01"
            onChange={(event) => updateField('budgetAmount', Number(event.target.value))}
            required
            step="0.01"
            type="number"
            value={form.budgetAmount}
          />
        </label>
        <label className="grid content-start gap-1.5 text-xs font-medium text-muted-foreground">
          Currency
          <select
            className={fieldClass}
            onChange={(event) => updateField('currency', event.target.value as 'USD' | 'EUR')}
            value={form.currency}
          >
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
          </select>
        </label>
      </div>
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input
          checked={form.useRag}
          className="h-4 w-4 accent-primary"
          onChange={(event) => updateField('useRag', event.target.checked)}
          type="checkbox"
        />
        Use RAG methodology and historical context
      </label>
      {(allOptionsQuery.isError || filteredOptionsQuery.isError) ? (
        <p className="text-sm text-destructive">Failed to load MAS selector values.</p>
      ) : null}
      <Button className="gap-2" disabled={submitDisabled} type="submit">
        <Play className="h-4 w-4" />
        {isPending ? 'Running MAS analysis...' : 'Run MAS Analysis'}
      </Button>
    </form>
  );
}

function baseFilters(form: MasFormState, country: string, company: string) {
  return {
    dateFrom: form.dateFrom,
    dateTo: form.dateTo,
    country,
    tld: 'all',
    company,
    companyDomain: 'all',
    competitors: 'all',
    competitorDomain: 'all',
  };
}

function buildQuestion(form: MasFormState, country?: string, company?: string) {
  const companyLabel = company || 'selected company';
  const countryLabel = country || 'selected country';
  const budget = new Intl.NumberFormat('en').format(form.budgetAmount || 0);
  if (form.strategyMode === 'market_entry') {
    return `Analyze Market Entry for ${companyLabel} in ${countryLabel} from ${form.dateFrom} to ${form.dateTo} with ${budget} ${form.currency} budget.`;
  }
  return `Analyze Existing Presence strategy for ${companyLabel} in ${countryLabel} from ${form.dateFrom} to ${form.dateTo} with ${budget} ${form.currency} budget.`;
}
