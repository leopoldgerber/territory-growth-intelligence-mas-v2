import { fetchApi } from '@/lib/api/client';

export type HealthResponse = {
  status: string;
  service?: string;
  environment?: string;
  timestamp?: string;
  version?: string;
};

export type DbHealthResponse = {
  status: string;
  database?: string;
  latency_ms?: number;
};

export type MetaTablesResponse = {
  tables: string[];
  schema?: string;
};

export function getHealth() {
  return fetchApi<HealthResponse>('/health');
}

export function getDbHealth() {
  return fetchApi<DbHealthResponse>('/db/health');
}

export function getMetaTables() {
  return fetchApi<MetaTablesResponse>('/meta/tables');
}
