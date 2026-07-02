import { Database, Eye } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { MasEvidenceItem } from '@/lib/types/mas';


export function MasEvidencePanel({ evidenceItems }: { evidenceItems: MasEvidenceItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Evidence Used</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {evidenceItems.length === 0 ? (
          <p className="text-sm text-muted-foreground">No evidence items are available yet.</p>
        ) : evidenceItems.map((item) => (
          <details className="rounded-md border bg-background p-4" key={item.id}>
            <summary className="flex cursor-pointer list-none items-start justify-between gap-3">
              <div className="min-w-0 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  <p className="text-sm font-medium">{formatEvidenceType(item.evidence_type)}</p>
                  <Badge variant="outline">{item.confidence}</Badge>
                  <Badge variant="secondary">{item.source_type}</Badge>
                </div>
                <p className="text-sm leading-5 text-muted-foreground">{item.summary}</p>
              </div>
              <Eye className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            </summary>
            <div className="mt-3 rounded-md bg-secondary/40 p-3">
              <div className="grid gap-2 text-xs text-muted-foreground md:grid-cols-2">
                <span>Source table: {item.source_table ?? 'Not set'}</span>
                <span>Source record: {item.source_record_id ?? 'Not set'}</span>
                <span>Created: {new Date(item.created_at).toLocaleString()}</span>
                <span>Context: {item.context_hash ?? 'Not set'}</span>
              </div>
              <pre className="mt-3 max-h-56 overflow-auto rounded-md border bg-background p-3 text-xs text-muted-foreground">
                {JSON.stringify(item.data_json, null, 2)}
              </pre>
            </div>
          </details>
        ))}
      </CardContent>
    </Card>
  );
}

function formatEvidenceType(value: string) {
  return value
    .split('_')
    .map((item) => item.charAt(0).toUpperCase() + item.slice(1))
    .join(' ');
}
