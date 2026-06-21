import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { listChartImages } from "../../api/chartImages";
import { generateWordReport, getWordReportOptions, listWordReports } from "../../api/wordReports";
import type { WordReportGeneratePayload } from "../../types/wordReport";
import { formatDate, formatNumber } from "../../utils/formatters";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Select, SelectOption } from "../ui/Select";

export function WordReportPanel({ formId }: { formId: string }) {
  const [includeChartImages, setIncludeChartImages] = useState(true);
  const [chartImageMode, setChartImageMode] =
    useState<WordReportGeneratePayload["chart_image_mode"]>("images_if_available");
  const [selectedImageIds, setSelectedImageIds] = useState<string[]>([]);

  const optionsQuery = useQuery({
    queryKey: ["word-report-options", formId],
    queryFn: () => getWordReportOptions(formId),
  });
  const imagesQuery = useQuery({
    queryKey: ["word-report-chart-images", formId],
    queryFn: () => listChartImages(formId),
  });
  const listQuery = useQuery({
    queryKey: ["word-reports", formId],
    queryFn: () => listWordReports(formId),
  });

  const mutation = useMutation({
    mutationFn: () =>
      generateWordReport(formId, {
        report_type: "full_form_report",
        source_type: "mixed",
        analysis_run_ids: [],
        orchestrated_analysis_run_id: null,
        title: "Informe de resultados estadisticos",
        subtitle: "Reporte generado por Colmena",
        decimals: 3,
        include_discarded: false,
        score_aggregation: "mean",
        include_charts_placeholders: true,
        include_chart_images: includeChartImages,
        chart_image_mode: chartImageMode,
        chart_image_artifact_ids: selectedImageIds,
        include_plain_language_explanations: true,
        include_technical_appendix: false,
        include_cover: true,
        include_methodology_summary: true,
        options: {},
      }),
    onSuccess: () => {
      void listQuery.refetch();
      void imagesQuery.refetch();
    },
  });

  if (optionsQuery.isLoading || imagesQuery.isLoading || listQuery.isLoading) {
    return <LoadingState label="Cargando modulo Word..." />;
  }

  if (optionsQuery.isError) {
    return <ErrorState message={(optionsQuery.error as Error).message} />;
  }

  if (imagesQuery.isError) {
    return <ErrorState message={(imagesQuery.error as Error).message} />;
  }

  if (listQuery.isError) {
    return <ErrorState message={(listQuery.error as Error).message} />;
  }

  const availableImages = imagesQuery.data?.items ?? [];

  const toggleSelectedImage = (artifactId: string) => {
    setSelectedImageIds((current) =>
      current.includes(artifactId) ? current.filter((item) => item !== artifactId) : [...current, artifactId],
    );
  };

  return (
    <div className="space-y-6">
      <Card className="space-y-4">
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-dark">Informe Word APA 7</h3>
          <p className="text-sm text-muted">
            Genera un `.docx` inicial usando corridas disponibles, tablas APA y recursos visuales guardados.
          </p>
          <p className="text-sm text-muted">
            Si el formulario ya tiene scoring ejecutado, el reporte incorporara resultados por baremo y advertencias de escalas de control.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="space-y-3 bg-surfaceSoft p-4">
            <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Modo visual</h4>
            <label className="flex items-center gap-3 text-sm text-dark">
              <input
                checked={includeChartImages}
                className="h-4 w-4 rounded border-border"
                onChange={(event) => setIncludeChartImages(event.target.checked)}
                type="checkbox"
              />
              Incluir imagenes reales si existen
            </label>
            <Select
              value={chartImageMode}
              onChange={(event) => setChartImageMode(event.target.value as WordReportGeneratePayload["chart_image_mode"])}
            >
              <SelectOption value="images_if_available">Usar imagenes si estan disponibles</SelectOption>
              <SelectOption value="placeholders_only">Usar solo placeholders</SelectOption>
              <SelectOption value="selected_images_only">Usar solo imagenes seleccionadas</SelectOption>
            </Select>
          </Card>

          <Card className="space-y-3 bg-surfaceSoft p-4">
            <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Imagenes del formulario</h4>
            <p className="text-sm text-muted">{availableImages.length} recursos visuales detectados.</p>
            {chartImageMode === "selected_images_only" ? (
              <div className="max-h-44 space-y-2 overflow-y-auto">
                {availableImages.length > 0 ? (
                  availableImages.map((image) => (
                    <label className="flex items-center gap-3 text-sm text-dark" key={image.artifact_id}>
                      <input
                        checked={selectedImageIds.includes(image.artifact_id)}
                        className="h-4 w-4 rounded border-border"
                        onChange={() => toggleSelectedImage(image.artifact_id)}
                        type="checkbox"
                      />
                      <span>{image.title || image.file_name}</span>
                    </label>
                  ))
                ) : (
                  <p className="text-sm text-muted">No hay imagenes guardadas todavia.</p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted">
                Puedes guardar PNG desde el editor de graficos y luego reutilizarlos aqui.
              </p>
            )}
          </Card>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button loading={mutation.isPending} onClick={() => mutation.mutate()}>
            Generar informe Word
          </Button>
          <p className="text-sm text-muted">
            Tipos disponibles: {optionsQuery.data?.available_report_types.join(", ") || "sin datos"}
          </p>
        </div>

        {mutation.isError ? <ErrorState message={(mutation.error as Error).message} /> : null}

        {mutation.data ? (
          <Card className="space-y-3 bg-surfaceSoft">
            <h4 className="text-base font-semibold text-dark">Ultimo reporte generado</h4>
            <p className="text-sm text-dark">{mutation.data.file_name}</p>
            <p className="text-sm text-muted">{mutation.data.file_path}</p>
            <p className="text-sm text-muted">
              {formatNumber(mutation.data.file_size_bytes / 1024, 1)} KB - {mutation.data.sections.length} secciones
            </p>
            <p className="text-sm text-muted">
              {mutation.data.chart_image_count} imagenes - {mutation.data.chart_placeholder_count} placeholders
            </p>
          </Card>
        ) : null}
      </Card>

      {listQuery.data && listQuery.data.length > 0 ? (
        <div className="grid gap-4">
          {listQuery.data.map((report) => (
            <Card className="space-y-2" key={report.artifact_id}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h4 className="text-base font-semibold text-dark">{report.file_name}</h4>
                  <p className="text-sm text-muted">{report.file_path}</p>
                </div>
                <p className="text-sm text-muted">{formatDate(report.created_at)}</p>
              </div>
              <p className="text-sm text-dark">
                {report.table_count} tablas - {report.chart_image_count} imagenes - {report.chart_placeholder_count} placeholders -{" "}
                {report.analysis_run_count} corridas
              </p>
              {report.warnings.length > 0 ? <p className="text-sm text-warning">{report.warnings.join(" - ")}</p> : null}
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          title="Aun no hay informes Word generados"
          description="Genera el primer documento para ver aqui la traza de exportaciones `.docx`."
        />
      )}
    </div>
  );
}
