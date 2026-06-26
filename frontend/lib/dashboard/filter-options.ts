import { readDashboardValues, writeDashboardValues } from '@/lib/dashboard/query-params';
import type { DomainFilterOption, FilterOption } from '@/lib/types/analytics';


export function filterDomainOptions(
  domains: DomainFilterOption[],
  companyValue: string,
  tldValue: string,
): DomainFilterOption[] {
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

export function sanitizeFilterSelection(
  value: string,
  options: FilterOption[],
  allowNone = false,
): string {
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
