import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { getAnalysisOptions, runAnalysis, runFullScan } from "../../api/analysis";
import type { AnalysisTarget, OrchestratedAnalysis } from "../../types/analysis";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Select, SelectOption } from "../ui/Select";
import { AnalysisSummary } from "./AnalysisSummary";

function flattenTargets(groups: Record<string, AnalysisTarget[]>) {
  const seen = new Map<string, AnalysisTarget>();
  Object.values(groups).forEach((items) => {
    items.forEach((item) => {
      const key = `${item.target_type}-${item.target_id}`;
      if (!seen.has(key)) {
        seen.set(key, item);
      }
    });
  });
  return Array.from(seen.values());
}

export function AnalysisRunner({ formId }: { formId: string }) {
  const [selectedX, setSelectedX] = useState("");
  const [selectedY, setSelectedY] = useState("");
  const [result, setResult] = useState<OrchestratedAnalysis | null>(null);

  const optionsQuery = useQuery({
    queryKey: ["analysis-options", formId],
    queryFn: () => getAnalysisOptions(formId),
  });

  const runMutation = useMutation({
    mutationFn: (payload: Parameters<typeof runAnalysis>[1]) => runAnalysis(formId, payload),
    onSuccess: setResult,
  });

  const scanMutation = useMutation({
    mutationFn: () =>
      runFullScan(formId, {
        alpha: 0.05,
        decimals: 3,
        include_discarded: false,
        score_aggregation: "mean",
        store_result: true,
        options: {
          max_targets: 10,
          max_pairwise_tests: 30,
          include_normality: true,
          include_descriptives: true,
          include_recommendations: true,
        },
      }),
    onSuccess: setResult,
  });

  const availableTargets = useMemo(
    () => (optionsQuery.data ? flattenTargets(optionsQuery.data.available_targets) : []),
    [optionsQuery.data],
  );

  if (optionsQuery.isLoading) {
    return <LoadingState label="Cargando opciones de analisis..." />;
  }

  if (optionsQuery.isError) {
    return <ErrorState message={(optionsQuery.error as Error).message} />;
  }

  if (!optionsQuery.data) {
    return (
      <EmptyState
        title="No hay opciones de analisis"
        description="El backend no devolvio configuracion para este formulario."
      />
    );
  }

  const correlationReady = selectedX && selectedY && selectedX !== selectedY;

  return (
    <div className="space-y-6">
      <Card className="space-y-4">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-dark">Analisis guiado</h3>
          <p className="text-sm text-muted">
            Ejecuta un flujo del orquestador sin salir del formulario. El backend decide la mejor ruta estadistica.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button
            loading={runMutation.isPending}
            onClick={() =>
              runMutation.mutate({
                analysis_goal: "descriptive_summary",
                targets: [],
                method: "auto",
                alpha: 0.05,
                decimals: 3,
                include_discarded: false,
                score_aggregation: "mean",
                store_result: true,
                options: {
                  include_normality: true,
                  include_descriptives: true,
                  include_recommendations: true,
                },
              })
            }
            variant="secondary"
          >
            Ejecutar resumen descriptivo
          </Button>
          <Button loading={scanMutation.isPending} onClick={() => scanMutation.mutate()}>
            Ejecutar scan general
          </Button>
        </div>

        <div className="grid gap-4 rounded-[24px] border border-border bg-[#fcfbf7] p-4 lg:grid-cols-[1fr_1fr_auto]">
          <Select value={selectedX} onChange={(event) => setSelectedX(event.target.value)}>
            <SelectOption value="">Selecciona variable X</SelectOption>
            {availableTargets.map((target) => (
              <SelectOption key={`${target.target_type}-${target.target_id}`} value={`${target.target_type}|${target.target_id}`}>
                {target.label}
              </SelectOption>
            ))}
          </Select>
          <Select value={selectedY} onChange={(event) => setSelectedY(event.target.value)}>
            <SelectOption value="">Selecciona variable Y</SelectOption>
            {availableTargets.map((target) => (
              <SelectOption key={`${target.target_type}-${target.target_id}`} value={`${target.target_type}|${target.target_id}`}>
                {target.label}
              </SelectOption>
            ))}
          </Select>
          <Button
            disabled={!correlationReady}
            loading={runMutation.isPending}
            onClick={() => {
              const [xType, xId] = selectedX.split("|");
              const [yType, yId] = selectedY.split("|");
              const xTarget = availableTargets.find((target) => target.target_id === xId && target.target_type === xType);
              const yTarget = availableTargets.find((target) => target.target_id === yId && target.target_type === yType);
              runMutation.mutate({
                analysis_goal: "correlation",
                targets: [
                  { target_type: xType, target_id: xId, role: "x", label: xTarget?.label },
                  { target_type: yType, target_id: yId, role: "y", label: yTarget?.label },
                ],
                method: "auto",
                alpha: 0.05,
                decimals: 3,
                include_discarded: false,
                score_aggregation: "mean",
                store_result: true,
                options: {
                  include_normality: true,
                  include_descriptives: true,
                  include_recommendations: true,
                },
              });
            }}
          >
            Ejecutar correlacion
          </Button>
        </div>
      </Card>

      {(runMutation.isError || scanMutation.isError) && (
        <ErrorState message={((runMutation.error || scanMutation.error) as Error).message} />
      )}

      <AnalysisSummary analysis={result} />
    </div>
  );
}
