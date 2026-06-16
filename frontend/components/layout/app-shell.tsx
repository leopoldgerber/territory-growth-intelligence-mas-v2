import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';

export function AppShell({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-screen bg-background" suppressHydrationWarning>
      <div className="grid min-h-screen lg:grid-cols-[260px_1fr]">
        <Sidebar />
        <div className="flex min-w-0 flex-col">
          <Topbar />
          {children}
        </div>
      </div>
    </div>
  );
}
