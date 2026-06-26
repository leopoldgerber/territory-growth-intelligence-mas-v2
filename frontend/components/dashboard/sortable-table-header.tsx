import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react';
import type { ReactNode } from 'react';

import type { SortDirection } from '@/lib/dashboard/table-sorting';


type SortableTableHeaderProps<Key extends string> = {
  activeKey: Key;
  align?: 'left' | 'right';
  children?: ReactNode;
  label: string;
  onSort: (key: Key) => void;
  sortDirection: SortDirection;
  sortKey: Key;
};

export function SortableTableHeader<Key extends string>({
  activeKey,
  align = 'left',
  children,
  label,
  onSort,
  sortDirection,
  sortKey,
}: SortableTableHeaderProps<Key>) {
  const isActive = activeKey === sortKey;
  const Icon = isActive ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown;

  return (
    <th className={`px-2 py-2 align-top font-medium ${align === 'right' ? 'text-right' : 'text-left'}`}>
      <span className={`flex items-center gap-1 ${align === 'right' ? 'justify-end' : 'justify-start'}`}>
        <button
          aria-label={`Sort by ${label}`}
          className={`inline-flex min-w-0 items-start gap-1 rounded-sm text-inherit transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 ${align === 'right' ? 'justify-end text-right' : 'justify-start text-left'}`}
          onClick={() => onSort(sortKey)}
          type="button"
        >
          <span className="whitespace-normal break-words text-xs leading-4">{label}</span>
          <Icon className="h-3.5 w-3.5 shrink-0" />
        </button>
        {children}
      </span>
    </th>
  );
}
