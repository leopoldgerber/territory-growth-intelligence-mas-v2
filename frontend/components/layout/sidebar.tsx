import Link from 'next/link';
import { BarChart3, Bell, BrainCircuit, FileText, Gauge, History, MessageSquareText, MonitorCheck, Upload } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

const navigationItems = [
  {
    title: 'System Status',
    href: '/system/status',
    icon: MonitorCheck,
    disabled: false,
  },
  {
    title: 'Data Upload',
    href: '/data-upload',
    icon: Upload,
    disabled: false,
  },
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: Gauge,
    disabled: false,
  },
  {
    title: 'Reports',
    href: '/reports/budget-strategy',
    icon: FileText,
    disabled: false,
  },
  {
    title: 'MAS Analysis',
    href: '/mas',
    icon: BrainCircuit,
    disabled: false,
  },
  {
    title: 'History',
    href: '/history',
    icon: History,
    disabled: false,
  },
  {
    title: 'Alerts',
    href: '/alerts',
    icon: Bell,
    disabled: false,
  },
  {
    title: 'Feedback',
    href: '/feedback',
    icon: MessageSquareText,
    disabled: false,
  },
];

export function Sidebar() {
  return (
    <aside className="hidden border-r bg-card/40 lg:block">
      <div className="flex h-full flex-col">
        <div className="space-y-2 px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">TGI</p>
              <p className="truncate text-xs text-muted-foreground">System foundation</p>
            </div>
          </div>
        </div>
        <Separator />
        <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const content = (
              <>
                <Icon className="h-4 w-4" />
                <span className="min-w-0 flex-1 truncate">{item.title}</span>
                {item.disabled ? <Badge variant="outline">Future</Badge> : null}
              </>
            );

            if (item.disabled) {
              return (
                <div
                  key={item.title}
                  className={cn(
                    'flex h-10 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground opacity-65',
                  )}
                >
                  {content}
                </div>
              );
            }

            return (
              <Link
                key={item.title}
                href={item.href}
                className="flex h-10 items-center gap-3 rounded-md bg-secondary px-3 text-sm font-medium"
              >
                {content}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
