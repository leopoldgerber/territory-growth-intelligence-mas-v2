'use client';

import { Wifi, WifiOff } from 'lucide-react';

import { useHealthQuery } from '@/lib/api/queries';
import { Badge } from '@/components/ui/badge';

export function BackendIndicator() {
  const healthQuery = useHealthQuery();

  if (healthQuery.isLoading) {
    return <Badge variant="outline">API check</Badge>;
  }

  if (healthQuery.isError) {
    return (
      <Badge variant="destructive">
        <WifiOff className="mr-1 h-3 w-3" />
        API offline
      </Badge>
    );
  }

  return (
    <Badge variant="success">
      <Wifi className="mr-1 h-3 w-3" />
      API online
    </Badge>
  );
}
