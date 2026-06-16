import { useQuery } from '@tanstack/react-query';

import { getDbHealth, getHealth, getMetaTables } from '@/lib/api/system';

export function useHealthQuery() {
  return useQuery({
    queryKey: ['system', 'health'],
    queryFn: getHealth,
  });
}

export function useDbHealthQuery() {
  return useQuery({
    queryKey: ['system', 'db-health'],
    queryFn: getDbHealth,
  });
}

export function useMetaTablesQuery() {
  return useQuery({
    queryKey: ['system', 'meta-tables'],
    queryFn: getMetaTables,
  });
}
