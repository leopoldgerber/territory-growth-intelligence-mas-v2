import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

type StatusCardProps = {
  title: string;
  description: string;
  isLoading: boolean;
  isError: boolean;
  children: React.ReactNode;
  errorMessage?: string;
};

export function StatusCard({ title, description, isLoading, isError, children, errorMessage }: StatusCardProps) {
  const statusBadge = isLoading ? (
    <Badge variant="outline">
      <Loader2 className="mr-1 h-3 w-3 animate-spin" />
      Loading
    </Badge>
  ) : isError ? (
    <Badge variant="destructive">
      <AlertCircle className="mr-1 h-3 w-3" />
      Error
    </Badge>
  ) : (
    <Badge variant="success">
      <CheckCircle2 className="mr-1 h-3 w-3" />
      Success
    </Badge>
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        {statusBadge}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-4/5" />
          </div>
        ) : isError ? (
          <p className="text-sm text-destructive">{errorMessage ?? 'Request failed'}</p>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}
