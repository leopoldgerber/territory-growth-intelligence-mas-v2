import { AlertTriangle, CheckCircle2, Lightbulb, ListChecks, ShieldAlert } from 'lucide-react';
import type { ReactNode } from 'react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { MasSynthesisOutput } from '@/lib/types/mas';


export function MasStructuredAnswer({ output }: { output: MasSynthesisOutput | null }) {
  if (!output) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Structured Answer</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Run MAS analysis to generate an evidence-backed answer.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
          <div className="space-y-1">
            <CardTitle>Executive Summary</CardTitle>
            <p className="text-sm leading-6 text-muted-foreground">{output.executive_summary}</p>
          </div>
          <Badge variant="outline">{output.confidence}</Badge>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border bg-primary/10 p-4">
            <p className="text-sm font-medium text-primary">Final Recommendation</p>
            <p className="mt-2 text-sm leading-6">{output.final_recommendation}</p>
          </div>
        </CardContent>
      </Card>
      <div className="grid gap-4 xl:grid-cols-2">
        <AnswerList
          icon={<CheckCircle2 className="h-4 w-4 text-primary" />}
          items={output.key_findings.map((item) => ({
            title: item.finding,
            meta: item.confidence,
            refs: item.evidence_refs,
          }))}
          title="Key Findings"
        />
        <AnswerList
          icon={<ListChecks className="h-4 w-4 text-primary" />}
          items={output.recommended_next_actions.map((item) => ({
            title: item.action,
            meta: item.priority,
            refs: item.evidence_refs,
          }))}
          title="Recommended Next Actions"
        />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Reasoning</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {output.reasoning_sections.map((section) => (
            <div className="rounded-md border bg-background p-4" key={section.title}>
              <div className="flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-primary" />
                <p className="text-sm font-medium">{section.title}</p>
              </div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{section.content}</p>
              <EvidenceRefs refs={section.evidence_refs} />
            </div>
          ))}
        </CardContent>
      </Card>
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Risks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {output.risks.length === 0 ? (
              <p className="text-sm text-muted-foreground">No explicit risks were returned.</p>
            ) : output.risks.map((risk) => (
              <div className="rounded-md border bg-background p-4" key={risk.risk}>
                <div className="flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-destructive" />
                  <p className="text-sm font-medium">{risk.risk}</p>
                  <Badge variant="outline">{risk.severity}</Badge>
                </div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{risk.mitigation}</p>
                <EvidenceRefs refs={risk.evidence_refs} />
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Limitations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {output.limitations.length === 0 ? (
              <p className="text-sm text-muted-foreground">No limitations were returned.</p>
            ) : output.limitations.map((item) => (
              <div className="flex gap-2 rounded-md border bg-background p-3 text-sm" key={item}>
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <span className="leading-5 text-muted-foreground">{item}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function AnswerList({
  icon,
  items,
  title,
}: {
  icon: ReactNode;
  items: Array<{ title: string; meta: string; refs: string[] }>;
  title: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No items were returned.</p>
        ) : items.map((item) => (
          <div className="rounded-md border bg-background p-4" key={item.title}>
            <div className="flex items-start gap-2">
              <span className="mt-0.5">{icon}</span>
              <div className="min-w-0 flex-1">
                <p className="text-sm leading-5">{item.title}</p>
                <Badge className="mt-2" variant="outline">{item.meta}</Badge>
              </div>
            </div>
            <EvidenceRefs refs={item.refs} />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function EvidenceRefs({ refs }: { refs: string[] }) {
  if (!refs.length) {
    return null;
  }
  return (
    <div className="mt-3 flex flex-wrap gap-1">
      {refs.map((ref) => (
        <Badge className="max-w-full truncate" key={ref} variant="secondary">
          {ref}
        </Badge>
      ))}
    </div>
  );
}
