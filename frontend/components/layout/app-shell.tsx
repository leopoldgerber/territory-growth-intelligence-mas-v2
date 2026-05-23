'use client';

import { useEffect, useState } from 'react';

import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';

export function AppShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return (
    <div className="min-h-screen bg-background" suppressHydrationWarning>
      {isMounted ? (
        <div className="grid min-h-screen lg:grid-cols-[260px_1fr]">
          <Sidebar />
          <div className="flex min-w-0 flex-col">
            <Topbar />
            {children}
          </div>
        </div>
      ) : null}
    </div>
  );
}
