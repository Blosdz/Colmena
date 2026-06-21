import { AlertTriangle } from "lucide-react";

import { Card } from "../../ui/Card";

export function ChartWarningPanel({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <Card className="space-y-3 border-warning/25 bg-warning/5">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-warning" />
        <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-warning">Advertencias</h4>
      </div>
      <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-dark">
        {warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
    </Card>
  );
}
