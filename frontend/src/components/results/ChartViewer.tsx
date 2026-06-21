import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { getRecommendedCharts } from "../../api/charts";
import type { ChartSpec } from "../../types/chart";
import { getChartTypeLabel } from "../../utils/chartFormatters";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Select, SelectOption } from "../ui/Select";
import { ChartEditor } from "./chart-editor/ChartEditor";
import { ChartImageGallery } from "./ChartImageGallery";

export function ChartViewer({ formId }: { formId: string }) {
  const [theme, setTheme] = useState("colmena_premium");
  const [activeChartId, setActiveChartId] = useState("");
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["recommended-charts", formId, theme],
    queryFn: () => getRecommendedCharts(formId, { theme, max_charts: 10 }),
  });

  useEffect(() => {
    if (!data?.charts.length) {
      setActiveChartId("");
      return;
    }

    setActiveChartId((current) =>
      current && data.charts.some((chart) => chart.chart_id === current) ? current : data.charts[0].chart_id,
    );
  }, [data]);

  const activeChart = useMemo(
    () => data?.charts.find((chart) => chart.chart_id === activeChartId) ?? data?.charts[0] ?? null,
    [activeChartId, data],
  );

  if (isLoading) {
    return <LoadingState label="Generando graficos recomendados..." />;
  }

  if (isError) {
    return (
      <div className="space-y-4">
        <ErrorState message={(error as Error).message} />
        <Button onClick={() => refetch()} variant="secondary">
          Reintentar
        </Button>
      </div>
    );
  }

  if (!data || data.charts.length === 0) {
    return (
      <EmptyState
        title="Colmena aun no encontro graficos recomendados"
        description="Primero recolecta respuestas o ejecuta un analisis para que el backend pueda sugerir visualizaciones."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-dark">Editor visual de graficos</h3>
          <p className="text-sm text-muted">
            Edita la presentacion del resultado sin reescribir la logica estadistica del backend.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Select className="w-[220px]" value={theme} onChange={(event) => setTheme(event.target.value)}>
            <SelectOption value="colmena_premium">Colmena premium</SelectOption>
            <SelectOption value="academic_light">Academico claro</SelectOption>
            <SelectOption value="presentation_clean">Presentacion limpia</SelectOption>
            <SelectOption value="monochrome_apa">Monocromo APA</SelectOption>
          </Select>
          <Button loading={isFetching} onClick={() => refetch()} variant="secondary">
            Recargar recomendados
          </Button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[300px_minmax(0,1fr)]">
        <Card className="space-y-3 p-4">
          <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Graficos disponibles</h4>
          <div className="grid gap-2">
            {data.charts.map((chart: ChartSpec) => {
              const isActive = chart.chart_id === activeChart?.chart_id;
              return (
                <button
                  className={`rounded-2xl border px-4 py-3 text-left transition ${
                    isActive
                      ? "border-amber bg-surfaceSoft shadow-card"
                      : "border-border bg-white hover:border-amber/30 hover:bg-[#fcfbf7]"
                  }`}
                  key={chart.chart_id}
                  onClick={() => setActiveChartId(chart.chart_id)}
                  type="button"
                >
                  <p className="text-sm font-semibold text-dark">{chart.title}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.14em] text-muted">
                    {getChartTypeLabel(chart.chart_type)}
                  </p>
                  <p className="mt-2 text-xs leading-5 text-muted">
                    {chart.description}
                  </p>
                </button>
              );
            })}
          </div>
        </Card>

        {activeChart ? (
          <ChartEditor chart={activeChart} storageKey={`colmena.chartEditor.${formId}.${activeChart.chart_id}`} />
        ) : null}
      </div>

      <ChartImageGallery formId={formId} />
    </div>
  );
}
