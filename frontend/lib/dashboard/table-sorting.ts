import { useMemo, useState } from 'react';


export type SortDirection = 'asc' | 'desc';

export type SortState<Key extends string> = {
  direction: SortDirection;
  key: Key;
};

export type SortValue = Date | null | number | string | undefined;

export type SortColumn<Row, Key extends string> = {
  getValue: (row: Row, index: number) => SortValue;
  key: Key;
};

function normalize_value(value: SortValue): number | string {
  if (value === null || value === undefined) {
    return '';
  }
  if (value instanceof Date) {
    return value.getTime();
  }
  if (typeof value === 'number') {
    return Number.isNaN(value) ? 0 : value;
  }
  return value.toLowerCase();
}

function compare_values(firstValue: SortValue, secondValue: SortValue): number {
  const firstComparable = normalize_value(firstValue);
  const secondComparable = normalize_value(secondValue);

  if (typeof firstComparable === 'number' && typeof secondComparable === 'number') {
    return firstComparable - secondComparable;
  }

  return String(firstComparable).localeCompare(String(secondComparable), undefined, {
    numeric: true,
    sensitivity: 'base',
  });
}

export function useTableSort<Row, Key extends string>(
  rows: Row[],
  columns: SortColumn<Row, Key>[],
  initialSort: SortState<Key>,
): {
  requestSort: (key: Key) => void;
  sortedRows: Row[];
  sortState: SortState<Key>;
} {
  const [sortState, setSortState] = useState<SortState<Key>>(initialSort);
  const sortedRows = useMemo(() => {
    const column = columns.find((item) => item.key === sortState.key);

    if (!column) {
      return rows;
    }

    return rows
      .map((row, index) => ({ index, row }))
      .sort((firstItem, secondItem) => {
        const comparedValue = compare_values(
          column.getValue(firstItem.row, firstItem.index),
          column.getValue(secondItem.row, secondItem.index),
        );
        const stableValue = comparedValue === 0 ? firstItem.index - secondItem.index : comparedValue;
        return sortState.direction === 'asc' ? stableValue : -stableValue;
      })
      .map((item) => item.row);
  }, [columns, rows, sortState.direction, sortState.key]);

  function requestSort(key: Key): void {
    setSortState((currentState) => ({
      direction: currentState.key === key && currentState.direction === 'asc' ? 'desc' : 'asc',
      key,
    }));
  }

  return { requestSort, sortedRows, sortState };
}
