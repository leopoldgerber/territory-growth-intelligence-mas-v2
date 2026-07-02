import { Badge } from '@/components/ui/badge';
import type { MasRunStatus } from '@/lib/types/mas';


const statusLabels: Record<MasRunStatus, string> = {
  pending: 'Pending',
  running: 'Running',
  needs_clarification: 'Needs clarification',
  completed: 'Completed',
  partial: 'Partial',
  failed: 'Failed',
  skipped: 'Skipped',
  cancelled: 'Cancelled',
};

export function MasStatusBadge({ status }: { status: MasRunStatus }) {
  const variant = status === 'completed'
    ? 'success'
    : status === 'partial' || status === 'needs_clarification'
      ? 'warning'
      : status === 'failed' || status === 'cancelled'
        ? 'destructive'
        : 'secondary';
  return <Badge variant={variant}>{statusLabels[status] ?? status}</Badge>;
}
