import { AlertTriangle } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';


export function MasWarningsPanel({
  error,
  questions,
  warnings,
}: {
  error?: string | null;
  questions?: string[];
  warnings?: string[];
}) {
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>MAS analysis failed</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }
  if (questions?.length) {
    return (
      <Alert>
        <AlertTitle>Clarification needed</AlertTitle>
        <AlertDescription>
          <ul className="mt-2 space-y-1">
            {questions.map((question) => (
              <li className="flex gap-2" key={question}>
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <span>{question}</span>
              </li>
            ))}
          </ul>
        </AlertDescription>
      </Alert>
    );
  }
  if (!warnings?.length) {
    return null;
  }
  return (
    <Alert>
      <AlertTitle>Analysis completed with warnings</AlertTitle>
      <AlertDescription>
        <ul className="mt-2 space-y-1">
          {warnings.map((warning) => (
            <li className="flex gap-2" key={warning}>
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
              <span>{warning}</span>
            </li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}
