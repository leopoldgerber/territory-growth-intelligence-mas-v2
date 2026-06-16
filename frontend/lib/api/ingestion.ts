import { fetchApi } from '@/lib/api/client';

export type IngestionRun = {
  id: string;
  run_id: string;
  project_id: string;
  file_name: string;
  file_type: string;
  file_extension: string | null;
  file_size_bytes: number | null;
  checksum: string | null;
  stored_file_path: string | null;
  status: string;
  progress_stage: string | null;
  progress_percent: number;
  period_start: string | null;
  period_end: string | null;
  row_count: number | null;
  valid_row_count: number | null;
  invalid_row_count: number | null;
  inserted_row_count: number | null;
  skipped_duplicate_count: number | null;
  failed_row_count: number | null;
  company_count: number | null;
  domain_count: number | null;
  country_count: number | null;
  ingestion_status: string;
  validation_status: string;
  error_message: string | null;
  worker_name: string | null;
  created_at: string | null;
  updated_at: string | null;
  queued_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  allowed_extensions?: string[];
};

export type IngestionError = {
  id: number;
  ingestion_run_id: string;
  row_number: number;
  column_name: string;
  error_code: string;
  error_message: string;
  raw_value: string | null;
  created_at: string | null;
};

export type IngestionRunsResponse = {
  runs: IngestionRun[];
};

export type IngestionErrorsResponse = {
  errors: IngestionError[];
};

export type FileTypesResponse = {
  file_types: string[];
};

export type UploadAcceptedResponse = {
  run_id: string;
  status: string;
  message: string;
};

export function getFileTypes() {
  return fetchApi<FileTypesResponse>('/ingestion/file-types');
}

export function getIngestionRuns() {
  return fetchApi<IngestionRunsResponse>('/ingestion/runs');
}

export function getIngestionRun(runId: string) {
  return fetchApi<IngestionRun>(`/ingestion/runs/${runId}`);
}

export function getIngestionErrors(runId: string) {
  return fetchApi<IngestionErrorsResponse>(`/ingestion/runs/${runId}/errors`);
}

export async function uploadIngestion(fileType: string, file: File): Promise<UploadAcceptedResponse> {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
  const formData = new FormData();
  formData.append('file_type', fileType);
  formData.append('file', file);

  const response = await fetch(`${apiBaseUrl}/ingestion/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}`);
  }

  const data = (await response.json()) as UploadAcceptedResponse;
  return data;
}
