import type { MasRunStatus } from '@/lib/types/mas';


export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return 'Not set';
  }
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export function formatStrategy(value: string | null | undefined) {
  if (value === 'market_entry') {
    return 'Market Entry';
  }
  if (value === 'existing_presence') {
    return 'Existing Presence';
  }
  return 'Not set';
}

export function statusTone(status: MasRunStatus) {
  if (status === 'completed') {
    return 'text-primary';
  }
  if (status === 'partial' || status === 'needs_clarification') {
    return 'text-accent';
  }
  if (status === 'failed' || status === 'cancelled') {
    return 'text-destructive';
  }
  return 'text-muted-foreground';
}
