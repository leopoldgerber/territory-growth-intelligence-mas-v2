import { DashboardFilters } from '@/components/dashboard/dashboard-filters';
import { DashboardIntelligenceTabs } from '@/components/dashboard/dashboard-intelligence-tabs';
import { Badge } from '@/components/ui/badge';

export default function DashboardPage() {
  return (
    <main className="flex w-full flex-1 flex-col">
      <section className="px-4 py-6 md:px-6">
        <div className="space-y-3">
          <Badge variant="secondary">Dashboard</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-normal text-foreground">Market exploration dashboard</h1>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Manual analytics workspace for country and competitor market exploration.
            </p>
          </div>
        </div>
      </section>
      <DashboardFilters />
      <section className="grid gap-5 px-4 py-5 md:px-6">
        <DashboardIntelligenceTabs />
      </section>
    </main>
  );
}
