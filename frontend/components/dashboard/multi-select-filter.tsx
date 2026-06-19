'use client';

import { Check, ChevronDown } from 'lucide-react';
import { useEffect, useRef } from 'react';

import { readDashboardValues, writeDashboardValues } from '@/lib/dashboard/query-params';
import type { FilterOption } from '@/lib/types/analytics';

type MultiSelectFilterProps = {
  allowNone?: boolean;
  disabled?: boolean;
  label: string;
  onChange: (value: string) => void;
  options: FilterOption[];
  value: string;
};

export function MultiSelectFilter({
  allowNone = false,
  disabled = false,
  label,
  onChange,
  options,
  value,
}: MultiSelectFilterProps) {
  const detailsRef = useRef<HTMLDetailsElement>(null);
  const isAll = value === 'all';
  const isNone = value === 'none';
  const selectedValues = isAll || isNone ? [] : readDashboardValues(value);
  const selectedSet = new Set(selectedValues);
  const selectedOptions = options.filter((option) => selectedSet.has(option.value));
  const summary = isAll
    ? 'All'
    : isNone
      ? 'None'
      : selectedOptions.length === 0
        ? 'None'
      : selectedOptions.length === 1
        ? selectedOptions[0].label
        : `${selectedOptions.length} selected`;

  useEffect(() => {
    function closeDropdown(event: PointerEvent): void {
      if (detailsRef.current && !detailsRef.current.contains(event.target as Node)) {
        detailsRef.current.open = false;
      }
    }

    function closeOnEscape(event: KeyboardEvent): void {
      if (event.key === 'Escape' && detailsRef.current) {
        detailsRef.current.open = false;
      }
    }

    document.addEventListener('pointerdown', closeDropdown);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeDropdown);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, []);

  function toggleOption(optionValue: string): void {
    const nextValues = selectedSet.has(optionValue)
      ? selectedValues.filter((item) => item !== optionValue)
      : [...selectedValues, optionValue];
    onChange(writeDashboardValues(nextValues));
  }

  return (
    <div className="grid gap-1.5 text-xs font-medium text-muted-foreground">
      <span>{label}</span>
      <details ref={detailsRef} className="group relative" data-disabled={disabled || undefined}>
        <summary className="flex h-9 cursor-pointer list-none items-center justify-between gap-2 rounded-md border border-input bg-background px-3 text-sm font-normal text-foreground outline-none transition-colors hover:bg-secondary group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50">
          <span className="truncate">{summary}</span>
          <ChevronDown className="h-4 w-4 shrink-0 transition-transform group-open:rotate-180" />
        </summary>
        <div className="absolute z-30 mt-1 max-h-64 w-full min-w-56 overflow-y-auto rounded-md border bg-background p-1 shadow-lg">
          <button
            className="flex w-full items-center gap-2 rounded-sm px-2 py-2 text-left text-sm font-normal text-foreground hover:bg-secondary"
            onClick={() => onChange('all')}
            type="button"
          >
            <span className="flex h-4 w-4 items-center justify-center rounded-sm border">
              {isAll ? <Check className="h-3 w-3" /> : null}
            </span>
            All
          </button>
          {allowNone ? (
            <button
              className="flex w-full items-center gap-2 rounded-sm px-2 py-2 text-left text-sm font-normal text-foreground hover:bg-secondary"
              onClick={() => onChange('none')}
              type="button"
            >
              <span className="flex h-4 w-4 items-center justify-center rounded-sm border">
                {isNone ? <Check className="h-3 w-3" /> : null}
              </span>
              None
            </button>
          ) : null}
          {options.map((option) => (
            <button
              key={option.value}
              className="flex w-full items-center gap-2 rounded-sm px-2 py-2 text-left text-sm font-normal text-foreground hover:bg-secondary"
              onClick={() => toggleOption(option.value)}
              type="button"
            >
              <span className="flex h-4 w-4 items-center justify-center rounded-sm border">
                {selectedSet.has(option.value) ? <Check className="h-3 w-3" /> : null}
              </span>
              <span className="truncate">{option.label}</span>
            </button>
          ))}
        </div>
      </details>
    </div>
  );
}
