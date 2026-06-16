'use client';

import { ChangeEvent, FormEvent, useMemo, useState } from 'react';
import { AlertCircle, FileUp, RefreshCw } from 'lucide-react';

import { IngestionError, IngestionRun } from '@/lib/api/ingestion';
import {
  useFileTypesQuery,
  useIngestionErrorsQuery,
  useIngestionRunQuery,
  useIngestionRunsQuery,
  useUploadMutation,
} from '@/lib/api/ingestion-queries';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';

const fallbackFileTypes = ['traffic_countries', 'traffic_sources', 'journey_sources', 'trend_by_devices'];

export function DataUpload() {
  const fileTypesQuery = useFileTypesQuery();
  const runsQuery = useIngestionRunsQuery();
  const uploadMutation = useUploadMutation();
  const [selectedFileType, setSelectedFileType] = useState('traffic_countries');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const selectedRunQuery = useIngestionRunQuery(selectedRunId);
  const errorsQuery = useIngestionErrorsQuery(selectedRunId);
  const fileTypes = fileTypesQuery.data?.file_types ?? fallbackFileTypes;
  const latestRun = selectedRunQuery.data ?? (selectedRunId === null ? (runsQuery.data?.runs[0] ?? null) : null);
  const selectedErrors = errorsQuery.data?.errors ?? [];

  const expectedSchemaText = useMemo(() => {
    if (selectedFileType === 'traffic_countries') {
      return 'date, company, domain, country';
    }
    if (selectedFileType === 'journey_sources') {
      return 'date, company, domain, source_type';
    }
    return 'date, company, domain';
  }, [selectedFileType]);

  function changeFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
  }

  function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedFile === null) {
      return;
    }
    uploadMutation.mutate(
      { fileType: selectedFileType, file: selectedFile },
      {
        onSuccess: (response) => {
          setSelectedRunId(response.run_id);
        },
      },
    );
  }

  function refreshRuns() {
    void runsQuery.refetch();
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-8">
      <section className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div className="space-y-2">
          <Badge variant="secondary">Data Upload</Badge>
          <h1 className="text-2xl font-semibold tracking-normal md:text-3xl">Controlled ingestion pipeline</h1>
          <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
            Upload CSV or XLSX files into the local validation and audit pipeline.
          </p>
        </div>
        <Button type="button" variant="outline" onClick={refreshRuns}>
          <RefreshCw className="h-4 w-4" />
          Refresh history
        </Button>
      </section>

      <section className="grid gap-4 lg:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Upload file</CardTitle>
            <CardDescription>Supported formats: .csv and .xlsx</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={submitUpload}>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="file-type">
                  File type
                </label>
                <select
                  id="file-type"
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  value={selectedFileType}
                  onChange={(event) => setSelectedFileType(event.target.value)}
                >
                  {fileTypes.map((fileType) => (
                    <option key={fileType} value={fileType}>
                      {fileType}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="upload-file">
                  Source file
                </label>
                <input
                  id="upload-file"
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={changeFile}
                />
              </div>

              <Alert>
                <AlertTitle>Expected required columns</AlertTitle>
                <AlertDescription>{expectedSchemaText}</AlertDescription>
              </Alert>

              <Button className="w-full" disabled={selectedFile === null || uploadMutation.isPending} type="submit">
                <FileUp className="h-4 w-4" />
                {uploadMutation.isPending ? 'Uploading' : 'Upload and validate'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <UploadResult
          run={latestRun}
          isLoading={uploadMutation.isPending || (selectedRunId !== null && selectedRunQuery.isLoading)}
          acceptedMessage={uploadMutation.data?.message ?? null}
          errorMessage={readError(uploadMutation.error)}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_420px]">
        <RunHistory
          runs={runsQuery.data?.runs ?? []}
          isLoading={runsQuery.isLoading}
          selectedRunId={selectedRunId}
          onSelectRun={setSelectedRunId}
        />
        <ValidationErrors errors={selectedErrors} isLoading={errorsQuery.isLoading} />
      </section>
    </main>
  );
}

function UploadResult({
  run,
  isLoading,
  acceptedMessage,
  errorMessage,
}: {
  run: IngestionRun | null;
  isLoading: boolean;
  acceptedMessage: string | null;
  errorMessage: string | null;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Upload result</CardTitle>
          <CardDescription>Uploading, validating, and inserting rows</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-4/5" />
        </CardContent>
      </Card>
    );
  }

  if (errorMessage !== null) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Upload failed</AlertTitle>
        <AlertDescription>{errorMessage}</AlertDescription>
      </Alert>
    );
  }

  if (run === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Upload result</CardTitle>
          <CardDescription>No upload has been selected yet</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Choose a file type and upload a CSV or XLSX file.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle>Upload result</CardTitle>
          <CardDescription>{acceptedMessage ?? run.file_name}</CardDescription>
        </div>
        <Badge variant={getStatusVariant(run.status)}>{run.status}</Badge>
      </CardHeader>
      <CardContent>
        {run.error_message ? (
          <Alert className="mb-4" variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Ingestion error</AlertTitle>
            <AlertDescription>{run.error_message}</AlertDescription>
          </Alert>
        ) : null}
        <MetricGrid run={run} />
      </CardContent>
    </Card>
  );
}

function MetricGrid({ run }: { run: IngestionRun }) {
  const metrics = [
    ['File type', run.file_type],
    ['Stage', formatStage(run.progress_stage)],
    ['Progress', `${run.progress_percent ?? 0}%`],
    ['Period', [run.period_start, run.period_end].filter(Boolean).join(' - ') || 'not detected'],
    ['Rows total', run.row_count ?? 0],
    ['Rows inserted', run.inserted_row_count ?? 0],
    ['Duplicates skipped', run.skipped_duplicate_count ?? 0],
    ['Validation errors', run.invalid_row_count ?? 0],
  ];

  return (
    <dl className="grid gap-3 text-sm md:grid-cols-2">
      {metrics.map(([label, value]) => (
        <div key={label} className="rounded-md border p-3">
          <dt className="text-muted-foreground">{label}</dt>
          <dd className="mt-1 font-medium">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function RunHistory({
  runs,
  isLoading,
  selectedRunId,
  onSelectRun,
}: {
  runs: IngestionRun[];
  isLoading: boolean;
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Ingestion history</CardTitle>
        <CardDescription>Recent upload audit records</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? <Skeleton className="h-20 w-full" /> : null}
        {!isLoading && runs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No ingestion runs yet.</p>
        ) : null}
        {runs.map((run) => (
          <button
            key={run.id}
            className="w-full rounded-md border p-3 text-left text-sm transition-colors hover:bg-secondary"
            type="button"
            onClick={() => onSelectRun(run.id)}
          >
            <div className="flex items-center justify-between gap-3">
              <span className="truncate font-medium">{run.file_name}</span>
              <Badge variant={run.id === selectedRunId ? getStatusVariant(run.status) : 'outline'}>
                {run.status}
              </Badge>
            </div>
            <Separator className="my-2" />
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span>{run.file_type}</span>
              <span>{run.created_at ?? 'no timestamp'}</span>
              <span>{run.inserted_row_count ?? 0} inserted</span>
            </div>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}

function ValidationErrors({ errors, isLoading }: { errors: IngestionError[]; isLoading: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Validation errors</CardTitle>
        <CardDescription>Row-level errors for selected run</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? <Skeleton className="h-20 w-full" /> : null}
        {!isLoading && errors.length === 0 ? (
          <p className="text-sm text-muted-foreground">No errors selected.</p>
        ) : null}
        {errors.slice(0, 20).map((error) => (
          <div key={error.id} className="rounded-md border p-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium">Row {error.row_number}</span>
              <Badge variant="outline">{error.error_code}</Badge>
            </div>
            <p className="mt-2 text-muted-foreground">{error.error_message}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {error.column_name}: {error.raw_value ?? 'empty'}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function readError(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }
  return null;
}

function getStatusVariant(status: string) {
  if (status === 'success') {
    return 'success';
  }
  if (status === 'warning' || status === 'partial_success') {
    return 'warning';
  }
  if (status === 'failed' || status === 'cancelled') {
    return 'destructive';
  }
  return 'outline';
}

function formatStage(stage: string | null) {
  if (stage === null) {
    return 'not started';
  }
  return stage.replaceAll('_', ' ');
}
