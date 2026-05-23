'use client';

import { RefreshCw } from 'lucide-react';

import { StatusCard } from '@/components/system/status-card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useDbHealthQuery, useHealthQuery, useMetaTablesQuery } from '@/lib/api/queries';

function readError(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return 'Unknown request error';
}

export function SystemStatus() {
  const healthQuery = useHealthQuery();
  const dbHealthQuery = useDbHealthQuery();
  const metaTablesQuery = useMetaTablesQuery();
  const tables = metaTablesQuery.data?.tables ?? [];
  const hasAnyError = healthQuery.isError || dbHealthQuery.isError || metaTablesQuery.isError;

  function refetchSystem() {
    void healthQuery.refetch();
    void dbHealthQuery.refetch();
    void metaTablesQuery.refetch();
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-8">
      <section className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div className="space-y-2">
          <Badge variant="secondary">System status</Badge>
          <h1 className="text-2xl font-semibold tracking-normal md:text-3xl">Backend and database connectivity</h1>
          <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
            Current foundation checks for FastAPI, PostgreSQL, and applied table metadata.
          </p>
        </div>
        <Button type="button" variant="outline" onClick={refetchSystem}>
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </section>

      {hasAnyError ? (
        <Alert variant="destructive">
          <AlertTitle>Connection issue</AlertTitle>
          <AlertDescription>One or more system checks failed. Verify backend and database services.</AlertDescription>
        </Alert>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-3">
        <StatusCard
          title="Backend API"
          description="GET /health"
          isLoading={healthQuery.isLoading}
          isError={healthQuery.isError}
          errorMessage={readError(healthQuery.error)}
        >
          <dl className="space-y-3 text-sm">
            <div className="flex items-center justify-between gap-4">
              <dt className="text-muted-foreground">Status</dt>
              <dd className="font-medium">{healthQuery.data?.status}</dd>
            </div>
            <Separator />
            <div className="flex items-center justify-between gap-4">
              <dt className="text-muted-foreground">Service</dt>
              <dd className="truncate font-medium">{healthQuery.data?.service ?? 'FastAPI'}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="text-muted-foreground">Version</dt>
              <dd className="font-medium">{healthQuery.data?.version ?? 'not reported'}</dd>
            </div>
          </dl>
        </StatusCard>

        <StatusCard
          title="Database"
          description="GET /db/health"
          isLoading={dbHealthQuery.isLoading}
          isError={dbHealthQuery.isError}
          errorMessage={readError(dbHealthQuery.error)}
        >
          <dl className="space-y-3 text-sm">
            <div className="flex items-center justify-between gap-4">
              <dt className="text-muted-foreground">Status</dt>
              <dd className="font-medium">{dbHealthQuery.data?.status}</dd>
            </div>
            <Separator />
            <div className="flex items-center justify-between gap-4">
              <dt className="text-muted-foreground">Database</dt>
              <dd className="truncate font-medium">{dbHealthQuery.data?.database ?? 'PostgreSQL'}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="text-muted-foreground">Latency</dt>
              <dd className="font-medium">
                {dbHealthQuery.data?.latency_ms ? `${dbHealthQuery.data.latency_ms} ms` : 'not reported'}
              </dd>
            </div>
          </dl>
        </StatusCard>

        <StatusCard
          title="Tables metadata"
          description="GET /meta/tables"
          isLoading={metaTablesQuery.isLoading}
          isError={metaTablesQuery.isError}
          errorMessage={readError(metaTablesQuery.error)}
        >
          <div className="space-y-4">
            <dl className="space-y-3 text-sm">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted-foreground">Tables loaded</dt>
                <dd className="font-medium">{tables.length}</dd>
              </div>
              <Separator />
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted-foreground">Schema</dt>
                <dd className="font-medium">{metaTablesQuery.data?.schema ?? 'public'}</dd>
              </div>
            </dl>
            <div className="flex max-h-44 flex-wrap gap-2 overflow-auto">
              {tables.length > 0 ? (
                tables.map((tableName) => (
                  <Badge key={tableName} variant="outline">
                    {tableName}
                  </Badge>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No tables reported yet.</p>
              )}
            </div>
          </div>
        </StatusCard>
      </section>
    </main>
  );
}
