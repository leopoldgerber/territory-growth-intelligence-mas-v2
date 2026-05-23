'use client';

import { Circle } from 'lucide-react';

import { BackendIndicator } from '@/components/system/backend-indicator';
import { ThemeToggle } from '@/components/theme-toggle';
import { Badge } from '@/components/ui/badge';

export function Topbar() {
  const appEnvironment = process.env.NEXT_PUBLIC_APP_ENV ?? 'local';

  return (
    <header className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur">
      <div className="flex h-14 items-center justify-between gap-4 px-4 md:px-6">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Circle className="h-2.5 w-2.5 fill-primary text-primary" />
            <p className="truncate text-sm font-semibold">Territory Growth Intelligence</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <BackendIndicator />
          <Badge variant="secondary">{appEnvironment}</Badge>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
