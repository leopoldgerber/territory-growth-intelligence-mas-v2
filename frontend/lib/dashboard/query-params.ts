export type DashboardFilterKey =
  | 'dateFrom'
  | 'dateTo'
  | 'country'
  | 'tld'
  | 'company'
  | 'companyDomain'
  | 'competitors'
  | 'competitorDomain';

export type DashboardFilters = Record<DashboardFilterKey, string>;

export const dashboardFilterKeys: DashboardFilterKey[] = [
  'dateFrom',
  'dateTo',
  'country',
  'tld',
  'company',
  'companyDomain',
  'competitors',
  'competitorDomain',
];

export const defaultDashboardFilters: DashboardFilters = {
  dateFrom: '2025-01-01',
  dateTo: '2025-02-01',
  country: 'all',
  tld: 'all',
  company: 'all',
  companyDomain: 'all',
  competitors: 'all',
  competitorDomain: 'all',
};

export function readDashboardValues(value: string): string[] {
  if (!value || value === 'all') {
    return [];
  }

  return Array.from(new Set(value.split(',').map((item) => item.trim()).filter(Boolean)));
}

export function writeDashboardValues(values: string[]): string {
  const uniqueValues = Array.from(new Set(values.filter(Boolean)));
  return uniqueValues.length === 0 ? 'all' : uniqueValues.join(',');
}

export function readDashboardFilters(searchParams: URLSearchParams): DashboardFilters {
  const filters = {
    dateFrom: searchParams.get('dateFrom') ?? defaultDashboardFilters.dateFrom,
    dateTo: searchParams.get('dateTo') ?? defaultDashboardFilters.dateTo,
    country: searchParams.get('country') ?? defaultDashboardFilters.country,
    tld: searchParams.get('tld') ?? defaultDashboardFilters.tld,
    company: searchParams.get('company') ?? defaultDashboardFilters.company,
    companyDomain: searchParams.get('companyDomain') ?? defaultDashboardFilters.companyDomain,
    competitors: searchParams.get('competitors') ?? defaultDashboardFilters.competitors,
    competitorDomain: searchParams.get('competitorDomain') ?? defaultDashboardFilters.competitorDomain,
  };

  return filters;
}

export function cleanDashboardParams(searchParams: URLSearchParams): URLSearchParams {
  const params = new URLSearchParams(searchParams.toString());

  dashboardFilterKeys.forEach((key) => {
    const value = params.get(key);

    if (!value?.trim()) {
      params.set(key, defaultDashboardFilters[key]);
    }
  });

  return params;
}

export function ensureDashboardParams(searchParams: URLSearchParams): URLSearchParams {
  const params = new URLSearchParams(searchParams.toString());

  dashboardFilterKeys.forEach((key) => {
    if (!params.get(key)?.trim()) {
      params.set(key, defaultDashboardFilters[key]);
    }
  });

  return params;
}

export function updateDashboardParams(
  searchParams: URLSearchParams,
  updates: Partial<DashboardFilters>,
): URLSearchParams {
  const params = new URLSearchParams(searchParams.toString());

  Object.entries(updates).forEach(([key, value]) => {
    const nextValue = value?.trim();

    if (nextValue) {
      params.set(key, nextValue);
      return;
    }

    params.delete(key);
  });

  return cleanDashboardParams(params);
}

export function buildDashboardHref(pathname: string, searchParams: URLSearchParams): string {
  const params = cleanDashboardParams(searchParams);
  const queryString = params.toString();

  if (!queryString) {
    return pathname;
  }

  return `${pathname}?${queryString}`;
}
