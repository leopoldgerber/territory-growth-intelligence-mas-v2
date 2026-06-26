'use client';

import { Check, ChevronDown, Search, X } from 'lucide-react';
import { useEffect, useLayoutEffect, useRef, useState } from 'react';

import { readDashboardValues, writeDashboardValues } from '@/lib/dashboard/query-params';
import type { FilterOption } from '@/lib/types/analytics';

type MultiSelectFilterProps = {
  allowAll?: boolean;
  allowNone?: boolean;
  disabled?: boolean;
  label: string;
  onChange: (value: string) => void;
  options: FilterOption[];
  placeholder?: string;
  single?: boolean;
  value: string;
};

export function MultiSelectFilter({
  allowAll = true,
  allowNone = false,
  disabled = false,
  label,
  onChange,
  options,
  placeholder = 'None',
  single = false,
  value,
}: MultiSelectFilterProps) {
  const [searchValue, setSearchValue] = useState('');
  const detailsRef = useRef<HTMLDetailsElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const scrollPositionRef = useRef(0);
  const isAll = allowAll && value === 'all';
  const isNone = value === 'none';
  const selectedValues = isAll
    ? options.map((option) => option.value)
    : isNone
      ? []
      : readDashboardValues(value);
  const selectedSet = new Set(selectedValues);
  const selectedOptions = options.filter((option) => selectedSet.has(option.value));
  const normalizedSearch = searchValue.trim().toLowerCase();
  const filteredOptions = normalizedSearch
    ? options.filter((option) =>
        option.label.toLowerCase().includes(normalizedSearch)
        || option.value.toLowerCase().includes(normalizedSearch))
    : options;
  const summary = isAll
    ? 'All'
    : isNone
      ? 'None'
      : selectedOptions.length === 0
        ? placeholder
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

  useLayoutEffect(() => {
    if (!menuRef.current) {
      return;
    }

    menuRef.current.scrollTop = scrollPositionRef.current;
  }, [options, value]);

  function changeSelection(nextValue: string): void {
    scrollPositionRef.current = menuRef.current?.scrollTop ?? 0;
    onChange(nextValue);
  }

  function toggleOption(optionValue: string): void {
    if (single) {
      const clearedValue = allowNone ? 'none' : allowAll ? 'all' : '';
      changeSelection(selectedSet.has(optionValue) ? clearedValue : optionValue);
      setSearchValue('');
      if (detailsRef.current) {
        detailsRef.current.open = false;
      }
      return;
    }
    const nextValues = selectedSet.has(optionValue)
      ? selectedValues.filter((item) => item !== optionValue)
      : [...selectedValues, optionValue];
    if (nextValues.length === 0 && allowNone) {
      changeSelection('none');
      return;
    }
    const selectedAll = nextValues.length === options.length;
    changeSelection(selectedAll ? 'all' : writeDashboardValues(nextValues));
  }

  function clearSelection(): void {
    changeSelection(allowNone ? 'none' : allowAll ? 'all' : '');
    if (detailsRef.current) {
      detailsRef.current.open = false;
    }
  }

  return (
    <div className="grid gap-1.5 text-xs font-medium text-muted-foreground">
      <span>{label}</span>
      <div className="flex min-w-0 gap-1">
        <details
          ref={detailsRef}
          className="group relative min-w-0 flex-1"
          data-disabled={disabled || undefined}
          onToggle={(event) => {
            if (!event.currentTarget.open) {
              setSearchValue('');
            }
          }}
        >
        <summary className="flex h-9 cursor-pointer list-none items-center justify-between gap-2 rounded-md border border-input bg-background px-3 text-sm font-normal text-foreground outline-none transition-colors hover:bg-secondary group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50">
          <span className="truncate">{summary}</span>
          <ChevronDown className="h-4 w-4 shrink-0 transition-transform group-open:rotate-180" />
        </summary>
        <div
          className="absolute z-30 mt-1 max-h-64 w-full min-w-56 overflow-y-auto rounded-md border bg-background p-1 shadow-lg"
          ref={menuRef}
        >
          <div className="sticky top-0 z-10 bg-background p-1">
            <div className="flex h-8 items-center gap-2 rounded-md border border-input px-2">
              <Search className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <input
                aria-label={`Search ${label.toLowerCase()}`}
                className="min-w-0 flex-1 bg-transparent text-sm font-normal text-foreground outline-none placeholder:text-muted-foreground"
                onChange={(event) => setSearchValue(event.target.value)}
                onKeyDown={(event) => event.stopPropagation()}
                placeholder="Search..."
                type="search"
                value={searchValue}
              />
            </div>
          </div>
          {allowAll ? (
            <button
              className="flex w-full items-center gap-2 rounded-sm px-2 py-2 text-left text-sm font-normal text-foreground hover:bg-secondary"
              onClick={() => changeSelection('all')}
              type="button"
            >
              <span className="flex h-4 w-4 items-center justify-center rounded-sm border">
                {isAll ? <Check className="h-3 w-3" /> : null}
              </span>
              All
            </button>
          ) : null}
          {allowNone ? (
            <button
              className="flex w-full items-center gap-2 rounded-sm px-2 py-2 text-left text-sm font-normal text-foreground hover:bg-secondary"
              onClick={() => changeSelection('none')}
              type="button"
            >
              <span className="flex h-4 w-4 items-center justify-center rounded-sm border">
                {isNone ? <Check className="h-3 w-3" /> : null}
              </span>
              None
            </button>
          ) : null}
          {filteredOptions.map((option) => (
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
          {filteredOptions.length === 0 ? (
            <p className="px-2 py-3 text-sm font-normal text-muted-foreground">No matching values.</p>
          ) : null}
        </div>
        </details>
        {!isAll && !isNone && selectedOptions.length > 0 ? (
          <button
            aria-label={`Clear ${label.toLowerCase()}`}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-input bg-background text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
            disabled={disabled}
            onClick={clearSelection}
            title={`Clear ${label}`}
            type="button"
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>
    </div>
  );
}
