import { useQuery } from "@tanstack/react-query";

import { listFormExports } from "../../api/datasets";
import { listWordReports } from "../../api/wordReports";
import { formatDate, formatNumber } from "../../utils/formatters";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";

export function ExportList({ formId }: { formId: string }) {
  const datasetQuery = useQuery({
    queryKey: ["dataset-exports", formId],
    queryFn: () => listFormExports(formId),
  });
  const wordQuery = useQuery({
    queryKey: ["word-exports-panel", formId],
    queryFn: () => listWordReports(formId),
  });

  if (datasetQuery.isLoading || wordQuery.isLoading) {
    return <LoadingState label="Cargando exportaciones..." />;
  }

  if (datasetQuery.isError) {
    return <ErrorState message={(datasetQuery.error as Error).message} />;
  }

  if (wordQuery.isError) {
    return <ErrorState message={(wordQuery.error as Error).message} />;
  }

  const datasetItems = datasetQuery.data?.items ?? [];
  const wordItems = wordQuery.data ?? [];

  if (datasetItems.length === 0 && wordItems.length === 0) {
    return (
      <EmptyState
        title="No hay exportaciones registradas"
        description="Aqui apareceran los Excel, CSV e informes Word generados desde el formulario."
      />
    );
  }

  return (
    <div className="grid gap-4">
      {datasetItems.map((item) => (
        <Card className="space-y-2" key={item.id}>
          <h4 className="text-base font-semibold text-dark">{item.file_name}</h4>
          <p className="text-sm text-muted">{item.file_path}</p>
          <p className="text-sm text-dark">
            {item.artifact_type} · {formatNumber((item.file_size_bytes ?? 0) / 1024, 1)} KB
          </p>
          <p className="text-sm text-muted">{formatDate(item.created_at)}</p>
        </Card>
      ))}
      {wordItems.map((item) => (
        <Card className="space-y-2" key={item.artifact_id}>
          <h4 className="text-base font-semibold text-dark">{item.file_name}</h4>
          <p className="text-sm text-muted">{item.file_path}</p>
          <p className="text-sm text-dark">
            Word · {formatNumber(item.file_size_bytes / 1024, 1)} KB · {item.table_count} tablas
          </p>
          <p className="text-sm text-muted">{formatDate(item.created_at)}</p>
        </Card>
      ))}
    </div>
  );
}
