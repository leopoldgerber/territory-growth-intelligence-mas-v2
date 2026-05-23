import Link from 'next/link';
import { Activity, ArrowRight, Database, Server } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const systemItems = [
  {
    title: 'Backend API',
    description: 'FastAPI health endpoint',
    icon: Server,
  },
  {
    title: 'Database',
    description: 'PostgreSQL connection status',
    icon: Database,
  },
  {
    title: 'Tables metadata',
    description: 'Applied schema visibility',
    icon: Activity,
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-8">
      <section className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          <Badge variant="secondary">Frontend foundation</Badge>
          <div className="space-y-3">
            <h1 className="text-3xl font-semibold tracking-normal text-foreground md:text-4xl">
              Territory Growth Intelligence
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground">
              System foundation for validating the current backend and database contour.
            </p>
          </div>
          <Button asChild>
            <Link href="/system/status">
              Open system status
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Current scope</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>API health, database health, and table metadata checks are wired through the UI.</p>
            <p>Analytics modules stay out of scope for this cycle.</p>
          </CardContent>
        </Card>
      </section>
      <section className="grid gap-4 md:grid-cols-3">
        {systemItems.map((item) => {
          const Icon = item.icon;

          return (
            <Card key={item.title}>
              <CardHeader className="space-y-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-secondary text-primary">
                  <Icon className="h-4 w-4" />
                </div>
                <CardTitle>{item.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </section>
    </main>
  );
}
