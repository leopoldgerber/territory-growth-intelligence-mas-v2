import { DashboardFilters } from '@/components/dashboard/dashboard-filters';
import { IntelligenceSection } from '@/components/dashboard/intelligence-section';
import { Badge } from '@/components/ui/badge';

const countryItems = [
  'Country selector',
  'Period selector',
  'Total country traffic',
  'Active competitors',
  'Top competitors',
  'Competitor share',
  'Traffic trend',
  'Desktop / mobile split',
  'Bounce / no-bounce',
  'Engagement metrics',
  'Short market conclusion',
];

const futureSections = [
  {
    title: 'Competitor Intelligence',
    description: 'Coming in the next analytic stage.',
  },
  {
    title: 'Channel Intelligence',
    description: 'Coming in the next analytic stage.',
  },
  {
    title: 'Device Intelligence',
    description: 'Coming in the next analytic stage.',
  },
];

export default function DashboardPage() {
  return (
    <main className="flex w-full flex-1 flex-col">
      <section className="px-4 py-6 md:px-6">
        <div className="space-y-3">
          <Badge variant="secondary">Dashboard</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-normal text-foreground">Market exploration dashboard</h1>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Manual analytics workspace for market overview and the first Country Intelligence layer.
            </p>
          </div>
        </div>
      </section>
      <DashboardFilters />
      <section className="grid gap-5 px-4 py-5 md:px-6">
        <IntelligenceSection
          description="High-level market summary will be added after analytic endpoints are implemented."
          title="Market Overview"
        />
        <IntelligenceSection
          description="Country-level traffic and market analysis will be implemented in the Country Intelligence stage."
          title="Country Intelligence"
        >
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {countryItems.map((item) => (
              <div key={item} className="rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground">
                {item}
              </div>
            ))}
          </div>
        </IntelligenceSection>
        <div className="grid gap-4 xl:grid-cols-3">
          {futureSections.map((section) => (
            <IntelligenceSection
              key={section.title}
              description={section.description}
              status="future"
              title={section.title}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
