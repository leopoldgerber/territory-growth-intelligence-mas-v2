import Link from 'next/link';
import { ExternalLink } from 'lucide-react';

import { MasStatusBadge } from '@/components/mas/mas-status-badge';
import { formatDateTime, formatStrategy } from '@/components/mas/mas-format';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { MasRunSummary } from '@/lib/types/mas';


export function MasRecentRuns({ runs }: { runs: MasRunSummary[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent MAS Runs</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {runs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No saved MAS runs yet.</p>
        ) : runs.map((run) => (
          <div className="grid gap-3 rounded-md border bg-background p-4 lg:grid-cols-[1fr_auto]" key={run.id}>
            <div className="min-w-0 space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <MasStatusBadge status={run.status} />
                <span className="text-xs text-muted-foreground">{formatStrategy(run.strategy_mode)}</span>
                <span className="text-xs text-muted-foreground">{formatDateTime(run.created_at)}</span>
              </div>
              <p className="truncate text-sm font-medium">{run.final_summary || run.user_query}</p>
              <p className="text-xs text-muted-foreground">
                {run.country ?? 'No country'} · {run.company ?? 'No company'}
              </p>
            </div>
            <Button asChild className="gap-2" size="sm" variant="outline">
              <Link href={`/mas/runs/${run.id}`}>
                <ExternalLink className="h-4 w-4" />
                Open
              </Link>
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
