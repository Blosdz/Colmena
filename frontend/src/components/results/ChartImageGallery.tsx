import { useMutation, useQuery } from "@tanstack/react-query";

import { deleteChartImage, listChartImages } from "../../api/chartImages";
import { formatDate, formatNumber } from "../../utils/formatters";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";

export function ChartImageGallery({ formId }: { formId: string }) {
  const query = useQuery({
    queryKey: ["chart-images", formId],
    queryFn: () => listChartImages(formId),
  });
  const deleteMutation = useMutation({
    mutationFn: (artifactId: string) => deleteChartImage(formId, artifactId),
    onSuccess: () => query.refetch(),
  });

  if (query.isLoading) {
    return <LoadingState label="Cargando imagenes guardadas..." />;
  }

  if (query.isError) {
    return <ErrorState message={(query.error as Error).message} />;
  }

  if (!query.data || query.data.total === 0) {
    return (
      <EmptyState
        title="Aun no hay imagenes de graficos guardadas"
        description="Exporta un PNG o SVG desde el editor para dejarlo disponible en futuros informes Word."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-dark">Recursos visuales guardados</h3>
          <p className="text-sm text-muted">Estas imagenes pueden insertarse en Word cuando el modo de reporte lo permita.</p>
        </div>
        <Button loading={query.isFetching} onClick={() => query.refetch()} variant="secondary">
          Refrescar
        </Button>
      </div>
      <div className="grid gap-3">
        {query.data.items.map((item) => (
          <Card className="space-y-2 p-4" key={item.artifact_id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-dark">{item.title || item.file_name}</p>
                <p className="text-xs text-muted">{item.artifact_id}</p>
              </div>
              <p className="text-xs text-muted">{formatDate(item.created_at)}</p>
            </div>
            <p className="text-sm text-muted">
              {item.format.toUpperCase()} - {formatNumber(item.file_size_bytes / 1024, 1)} KB
            </p>
            <p className="text-xs text-muted">{item.file_path}</p>
            <div className="flex justify-end">
              <Button
                loading={deleteMutation.isPending}
                onClick={() => deleteMutation.mutate(item.artifact_id)}
                size="sm"
                variant="ghost"
              >
                Eliminar
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
