'use client';

import { useState, type FormEvent } from 'react';

import { Button } from '@/components/ui/button';
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

  function update_field<Key extends keyof BudgetStrategyGenerateRequest>(
    key: Key,
    value: BudgetStrategyGenerateRequest[Key],
  ): void {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function submit_form(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <form className="space-y-4 border-b pb-5" onSubmit={submit_form}>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
          Country
          <input className={fieldClass} onChange={(event) => update_field('country', event.target.value)} placeholder="ITA or Italy" required value={form.country} />
        </label>
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
        {([
          ['company', 'Company'],
          ['company_domain', 'Company Domain'],
          ['competitors', 'Competitors'],
          ['competitor_domain', 'Competitor Domain'],
          ['tld', 'TLD'],
        ] as const).map(([key, label]) => (
          <label className="grid gap-1.5 text-xs font-medium text-muted-foreground" key={key}>
            {label}
            <input className={fieldClass} onChange={(event) => update_field(key, event.target.value)} value={form[key]} />
          </label>
        ))}
      </div>
      <Button disabled={isPending} type="submit">
        {isPending ? 'Generating strategy...' : 'Generate budget strategy'}
      </Button>
    </form>
  );
}
