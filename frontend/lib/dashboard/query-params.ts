export type DashboardFilterKey = 'dateFrom' | 'dateTo' | 'country' | 'domain';

export type DashboardFilters = Record<DashboardFilterKey, string>;

export const dashboardFilterKeys: DashboardFilterKey[] = ['dateFrom', 'dateTo', 'country', 'domain'];

export const defaultDashboardFilters: DashboardFilters = {
  dateFrom: '2025-01-01',
  dateTo: '2025-02-01',
  country: 'all',
  domain: 'all',
};

export function readDashboardFilters(searchParams: URLSearchParams): DashboardFilters {
  const filters = {
    dateFrom: searchParams.get('dateFrom') ?? defaultDashboardFilters.dateFrom,
    dateTo: searchParams.get('dateTo') ?? defaultDashboardFilters.dateTo,
    country: searchParams.get('country') ?? defaultDashboardFilters.country,
    domain: searchParams.get('domain') ?? defaultDashboardFilters.domain,
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
