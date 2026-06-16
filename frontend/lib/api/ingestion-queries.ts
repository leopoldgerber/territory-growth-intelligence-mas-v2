import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  getFileTypes,
  getIngestionErrors,
  getIngestionRun,
  getIngestionRuns,
  uploadIngestion,
} from '@/lib/api/ingestion';

const terminalStatuses = ['success', 'partial_success', 'failed', 'cancelled'];

export function useFileTypesQuery() {
  return useQuery({
    queryKey: ['ingestion', 'file-types'],
    queryFn: getFileTypes,
  });
}

export function useIngestionRunsQuery() {
  return useQuery({
    queryKey: ['ingestion', 'runs'],
    queryFn: getIngestionRuns,
    refetchInterval: (query) => {
      const hasActiveRun = query.state.data?.runs.some((run) => !terminalStatuses.includes(run.status)) ?? false;
      return hasActiveRun ? 3000 : false;
    },
  });
}

export function useIngestionRunQuery(runId: string | null) {
  return useQuery({
    queryKey: ['ingestion', 'run', runId],
    queryFn: () => getIngestionRun(runId ?? ''),
    enabled: Boolean(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === undefined || terminalStatuses.includes(status)) {
        return false;
      }
      return 3000;
    },
  });
}

export function useIngestionErrorsQuery(runId: string | null) {
  return useQuery({
    queryKey: ['ingestion', 'errors', runId],
    queryFn: () => getIngestionErrors(runId ?? ''),
    enabled: Boolean(runId),
  });
}

export function useUploadMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ fileType, file }: { fileType: string; file: File }) => uploadIngestion(fileType, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['ingestion', 'runs'] });
    },
  });
}
