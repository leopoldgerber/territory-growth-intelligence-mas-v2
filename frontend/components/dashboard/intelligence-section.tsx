import type { ReactNode } from 'react';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

type IntelligenceSectionProps = {
  title: string;
  description: string;
  status?: 'active' | 'future';
  children?: ReactNode;
};

export function IntelligenceSection({
  title,
  description,
  status = 'active',
  children,
}: IntelligenceSectionProps) {
  return (
    <section
      className={cn(
        'rounded-md border bg-card/40 p-5',
        status === 'future' ? 'border-dashed opacity-75' : 'border-border',
      )}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold tracking-normal text-foreground">{title}</h2>
            {status === 'future' ? <Badge variant="outline">Future</Badge> : null}
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
      </div>
      {children ? <div className="mt-5">{children}</div> : null}
    </section>
  );
}
