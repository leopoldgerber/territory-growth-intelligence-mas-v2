'use client';

import { Flag, Users } from 'lucide-react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import type { KeyboardEvent } from 'react';

import { CompetitorIntelligenceSection } from '@/components/dashboard/competitor-intelligence/competitor-intelligence-section';
import { CountryIntelligenceSection } from '@/components/dashboard/country-intelligence/country-intelligence-section';
import { cn } from '@/lib/utils';

type IntelligenceTab = 'country' | 'competitor';

const intelligenceTabs: {
  id: IntelligenceTab;
  label: string;
}[] = [
  {
    id: 'country',
    label: 'Country Intelligence',
  },
  {
    id: 'competitor',
    label: 'Competitor Intelligence',
  },
];

function read_active_tab(value: string | null): IntelligenceTab {
  if (value === 'competitor') {
    return 'competitor';
  }
  return 'country';
}

export function DashboardIntelligenceTabs() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeTab = read_active_tab(searchParams.get('intelligence'));

  function update_active_tab(tab: IntelligenceTab): void {
    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.set('intelligence', tab);
    router.replace(`${pathname}?${nextParams.toString()}`, { scroll: false });
  }

  function handle_tab_key(event: KeyboardEvent<HTMLButtonElement>, currentIndex: number): void {
    let nextIndex = currentIndex;
    if (event.key === 'ArrowRight') {
      nextIndex = (currentIndex + 1) % intelligenceTabs.length;
    } else if (event.key === 'ArrowLeft') {
      nextIndex = (currentIndex - 1 + intelligenceTabs.length) % intelligenceTabs.length;
    } else if (event.key === 'Home') {
      nextIndex = 0;
    } else if (event.key === 'End') {
      nextIndex = intelligenceTabs.length - 1;
    } else {
      return;
    }

    event.preventDefault();
    const nextTab = intelligenceTabs[nextIndex];
    update_active_tab(nextTab.id);
    document.getElementById(`${nextTab.id}-intelligence-tab`)?.focus();
  }

  return (
    <div className="grid gap-4">
      <div aria-label="Dashboard intelligence views" className="border-b" role="tablist">
        <div className="flex min-w-0 gap-1 overflow-x-auto">
          {intelligenceTabs.map((tab, index) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.id === 'country' ? Flag : Users;

            return (
              <button
                aria-controls={`${tab.id}-intelligence-panel`}
                aria-selected={isActive}
                className={cn(
                  'flex h-10 shrink-0 items-center gap-2 border-b-2 px-3 text-sm font-medium transition-colors',
                  isActive
                    ? 'border-primary text-foreground'
                    : 'border-transparent text-muted-foreground hover:text-foreground',
                )}
                id={`${tab.id}-intelligence-tab`}
                key={tab.id}
                onClick={() => update_active_tab(tab.id)}
                onKeyDown={(event) => handle_tab_key(event, index)}
                role="tab"
                tabIndex={isActive ? 0 : -1}
                type="button"
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
      <div
        aria-labelledby={`${activeTab}-intelligence-tab`}
        id={`${activeTab}-intelligence-panel`}
        role="tabpanel"
      >
        {activeTab === 'country' ? <CountryIntelligenceSection /> : <CompetitorIntelligenceSection />}
      </div>
    </div>
  );
}
