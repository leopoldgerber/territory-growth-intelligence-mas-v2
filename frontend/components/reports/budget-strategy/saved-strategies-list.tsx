import { Button } from '@/components/ui/button';
import type { BudgetStrategyReport } from '@/lib/types/reports';


export function SavedStrategiesList({
  items,
  selectedId,
  onSelect,
}: {
  items: BudgetStrategyReport[];
  selectedId: number | null;
  onSelect: (reportId: number) => void;
}) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-foreground">Saved Strategies</h2>
      {items.length === 0 ? <p className="text-sm text-muted-foreground">No saved budget strategies.</p> : null}
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <Button className="h-auto justify-start px-3 py-3 text-left" key={item.id} onClick={() => onSelect(item.id)} type="button" variant={selectedId === item.id ? 'secondary' : 'outline'}>
            <span className="grid gap-1">
              <span className="text-sm font-medium">{item.country} · {item.budget_amount.toLocaleString()} {item.currency}</span>
              <span className="text-xs font-normal text-muted-foreground">{item.date_from} - {item.date_to} · {item.scope}</span>
            </span>
          </Button>
        ))}
      </div>
    </div>
  );
}
