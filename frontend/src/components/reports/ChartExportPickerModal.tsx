import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { Chart as ChartJS } from "chart.js";
import { Download, Loader2, X } from "lucide-react";
import JSZip from "jszip";

import { getBaremoResolution } from "../../api/scoring";
import {
  runPairCorrelation,
  uniqueCorrelationPairs,
  type CorrelationMatrixCell,
  type CorrelationMatrixReport,
  type CorrelationMethod,
  type NormalityReport,
  type NormalityTestResult,
  type ReliabilityReport,
  type ReliabilityTarget,
} from "../../api/reports";
import type { VariableBaremo } from "../../types/scoring";
import { AlphaBarChart } from "./AlphaBarChart";
import { BaremoLevelsChart } from "./BaremoLevelsChart";
import { CorrelationScatterChart, slugify } from "./CorrelationScatterChart";
import { NormalityHistogramCard } from "./NormalityHistogramCard";

interface ChartExportPickerModalProps {
  open: boolean;
  onClose: () => void;
  formId: string;
  variableReport: ReliabilityReport | undefined;
  dimensionReport: ReliabilityReport | undefined;
  normalityReport: NormalityReport | undefined;
  correlationReport: CorrelationMatrixReport | undefined;
  correlationMethod: CorrelationMethod;
}

function pairKey(cell: CorrelationMatrixCell): string {
  return `${cell.row_target_id}::${cell.column_target_id}`;
}

type CaptureSpec =
  | { kind: "reliability"; variableTargets: ReliabilityTarget[]; dimensionTargets: ReliabilityTarget[] }
  | { kind: "normality"; result: NormalityTestResult }
  | {
      kind: "correlation";
      cell: CorrelationMatrixCell;
      xValues: number[];
      yValues: number[];
      coefficient: number | null;
      pValue: number | null;
      methodUsed: string;
      alpha: number;
    }
  | { kind: "baremo"; item: VariableBaremo };

function specFileName(spec: CaptureSpec, order: number): string {
  const prefix = `${order.toString().padStart(2, "0")}`;
  if (spec.kind === "reliability") return `${prefix}-fiabilidad-alfa-cronbach.png`;
  if (spec.kind === "normality") return `${prefix}-normalidad-${slugify(spec.result.target_name)}.png`;
  if (spec.kind === "correlation") {
    return `${prefix}-correlacion-${slugify(spec.cell.row_label)}-vs-${slugify(spec.cell.column_label)}.png`;
  }
  return `${prefix}-baremo-${slugify(spec.item.variable_label)}.png`;
}

/** Máximo tiempo de espera para que todos los gráficos ocultos terminen de pintar; pasado ese
 * tiempo se continúa solo con lo capturado (mismo criterio "skip gracioso" del bundle anterior
 * cuando a un gráfico le faltaban datos). */
const CAPTURE_TIMEOUT_MS = 20000;

export function ChartExportPickerModal({
  open,
  onClose,
  formId,
  variableReport,
  dimensionReport,
  normalityReport,
  correlationReport,
  correlationMethod,
}: ChartExportPickerModalProps) {
  const [selectedPairs, setSelectedPairs] = useState<Set<string>>(new Set());
  const [selectedBaremos, setSelectedBaremos] = useState<Set<string>>(new Set());
  const [isExporting, setIsExporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [captureSpecs, setCaptureSpecs] = useState<CaptureSpec[] | null>(null);

  // `dataUrl` puede ser null: una captura fallida se registra igual para que
  // no se quede esperando al timeout, y se descarta al armar el ZIP.
  const capturedRef = useRef<Map<number, { name: string; dataUrl: string | null }>>(new Map());
  const settledRef = useRef(false);
  const specsRef = useRef<CaptureSpec[] | null>(null);
  const captureIdRef = useRef(0);

  const baremoQuery = useQuery({
    queryKey: ["chart-export-baremo-resolution", formId],
    queryFn: () => getBaremoResolution(formId),
    enabled: open && Boolean(formId),
  });

  const pairs = useMemo(
    () => (correlationReport ? uniqueCorrelationPairs(correlationReport) : []),
    [correlationReport],
  );
  const baremoItems = useMemo(
    () => (baremoQuery.data?.items ?? []).filter((item) => item.levels.length > 0),
    [baremoQuery.data],
  );

  const hasReliabilityData = useMemo(
    () =>
      [...(variableReport?.results ?? []), ...(dimensionReport?.results ?? [])].some(
        (target) => target.result.alpha !== null,
      ),
    [variableReport, dimensionReport],
  );
  const normalityResults = useMemo(
    () => (normalityReport?.results ?? []).filter((result) => result.valid_n >= 5),
    [normalityReport],
  );

  const totalCount =
    (hasReliabilityData ? 1 : 0) + normalityResults.length + selectedPairs.size + selectedBaremos.size;

  function finalize(specs: CaptureSpec[]) {
    if (settledRef.current) return;
    settledRef.current = true;

    // Ordenado por nombre: el prefijo numérico deja el ZIP en el mismo orden en
    // que se listan las gráficas.
    const images = [...capturedRef.current.values()]
      .filter((entry): entry is { name: string; dataUrl: string } => Boolean(entry.dataUrl))
      .sort((a, b) => a.name.localeCompare(b.name));
    specsRef.current = null;
    setCaptureSpecs(null);

    if (images.length < specs.length) {
      console.warn(
        `[ChartExportPickerModal] Solo se capturaron ${images.length} de ${specs.length} imágenes antes de continuar.`,
      );
    }

    if (images.length === 0) {
      setErrorMessage(
        "No se pudo capturar ninguna gráfica. Revisa la consola del navegador (F12) e inténtalo de nuevo.",
      );
      setIsExporting(false);
      return;
    }

    void (async () => {
      try {
        const zip = new JSZip();
        images.forEach(({ name, dataUrl }) => {
          const base64 = dataUrl.split(",")[1] ?? "";
          zip.file(name, base64, { base64: true });
        });
        const blob = await zip.generateAsync({ type: "blob" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `reportes-graficas-${formId}.zip`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        setIsExporting(false);
        onClose();
      } catch (error) {
        console.error("[ChartExportPickerModal] Error generando el ZIP", error);
        setErrorMessage("No se pudo generar el ZIP de gráficas. Intenta de nuevo.");
        setIsExporting(false);
      }
    })();
  }

  // Vigila el montaje oculto: si no termina de pintar dentro del tiempo límite,
  // se continúa con lo capturado hasta entonces en vez de colgar el export.
  useEffect(() => {
    if (!captureSpecs) return;
    const capturingId = captureIdRef.current;
    const timeoutId = setTimeout(() => {
      if (capturingId !== captureIdRef.current || !specsRef.current) return;
      console.warn("[ChartExportPickerModal] Tiempo de espera agotado capturando las gráficas.");
      finalize(specsRef.current);
    }, CAPTURE_TIMEOUT_MS);
    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [captureSpecs]);

  function registerCapture(index: number, spec: CaptureSpec, dataUrl: string | null) {
    capturedRef.current.set(index, { name: specFileName(spec, index + 1), dataUrl });
    const specs = specsRef.current;
    if (specs && capturedRef.current.size === specs.length) {
      finalize(specs);
    }
  }

  function handleChartReady(index: number, spec: CaptureSpec, chart: ChartJS) {
    // Un frame extra de margen para asegurar que el canvas ya pintó antes de leerlo.
    requestAnimationFrame(() => {
      let dataUrl: string | null = null;
      try {
        dataUrl = chart.toBase64Image();
      } catch (error) {
        console.error(`[ChartExportPickerModal] No se pudo capturar la gráfica #${index + 1}`, error);
      }
      registerCapture(index, spec, dataUrl);
    });
  }

  if (!open) return null;

  function togglePair(cell: CorrelationMatrixCell) {
    setSelectedPairs((prev) => {
      const next = new Set(prev);
      const key = pairKey(cell);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toggleBaremo(scoringConfigId: string) {
    setSelectedBaremos((prev) => {
      const next = new Set(prev);
      if (next.has(scoringConfigId)) next.delete(scoringConfigId);
      else next.add(scoringConfigId);
      return next;
    });
  }

  async function handleExport() {
    setErrorMessage(null);
    setIsExporting(true);
    try {
      const selectedPairCells = pairs.filter((cell) => selectedPairs.has(pairKey(cell)));
      const pairRuns = await Promise.all(
        selectedPairCells.map(async (cell) => {
          const run = await runPairCorrelation(formId, {
            x: { target_type: "project_variable", target_id: cell.row_target_id },
            y: { target_type: "project_variable", target_id: cell.column_target_id },
            method: correlationMethod,
          });
          return { cell, result: run.result };
        }),
      );

      const correlationAlpha = correlationReport?.alpha ?? 0.05;
      const specs: CaptureSpec[] = [
        ...(hasReliabilityData
          ? [
              {
                kind: "reliability" as const,
                variableTargets: variableReport?.results ?? [],
                dimensionTargets: dimensionReport?.results ?? [],
              },
            ]
          : []),
        ...normalityResults.map((result) => ({ kind: "normality" as const, result })),
        ...pairRuns
          .filter((run) => run.result.x_values && run.result.y_values && run.result.x_values.length > 0)
          .map((run) => ({
            kind: "correlation" as const,
            cell: run.cell,
            xValues: run.result.x_values as number[],
            yValues: run.result.y_values as number[],
            coefficient: run.result.coefficient,
            pValue: run.result.p_value,
            methodUsed: run.result.method_used,
            alpha: correlationAlpha,
          })),
        ...baremoItems
          .filter((item) => selectedBaremos.has(item.scoring_config_id))
          .map((item) => ({ kind: "baremo" as const, item })),
      ];

      if (specs.length === 0) {
        setErrorMessage("No hay gráficas disponibles para exportar.");
        setIsExporting(false);
        return;
      }

      capturedRef.current = new Map();
      settledRef.current = false;
      captureIdRef.current += 1;
      specsRef.current = specs;
      setCaptureSpecs(specs);
    } catch (error) {
      console.error("[ChartExportPickerModal] Error preparando el export", error);
      setErrorMessage("No se pudo generar el ZIP de gráficas. Intenta de nuevo.");
      setIsExporting(false);
    }
  }

  return (
    <>
      <div
        className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/40 p-4"
        onClick={() => !isExporting && onClose()}
      >
        <div
          className="flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-[20px] bg-white shadow-glass"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 className="text-base font-semibold text-dark">Exportar gráficas</h2>
            <button
              type="button"
              className="rounded-full p-1 text-muted transition-colors hover:text-dark disabled:cursor-not-allowed disabled:opacity-50"
              onClick={onClose}
              disabled={isExporting}
              aria-label="Cerrar"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 space-y-5 overflow-y-auto px-5 py-4">
            <p className="text-sm text-muted">
              Se incluyen automáticamente el gráfico de Alfa de Cronbach y los histogramas de
              normalidad. Elige qué pares de correlación y qué baremos quieres agregar al ZIP.
            </p>

            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.06em] text-muted">
                Pares de correlación
              </h3>
              {pairs.length === 0 ? (
                <p className="text-sm text-muted">No hay pares de correlación disponibles.</p>
              ) : (
                <div className="space-y-2">
                  {pairs.map((cell) => {
                    const key = pairKey(cell);
                    const active = selectedPairs.has(key);
                    return (
                      <label
                        key={key}
                        className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition-colors ${
                          active
                            ? "border-amber bg-amber/5 ring-1 ring-amber/30"
                            : "border-border hover:border-amber/40"
                        }`}
                      >
                        <input
                          type="checkbox"
                          className="h-4 w-4 shrink-0 accent-amber"
                          checked={active}
                          onChange={() => togglePair(cell)}
                        />
                        <span className="text-sm text-dark">
                          {cell.row_label} – {cell.column_label}
                        </span>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>

            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.06em] text-muted">Baremos</h3>
              {baremoQuery.isLoading ? (
                <p className="text-sm text-muted">Cargando baremos...</p>
              ) : baremoItems.length === 0 ? (
                <p className="text-sm text-muted">No hay baremos resueltos para este formulario.</p>
              ) : (
                <div className="space-y-2">
                  {baremoItems.map((item) => {
                    const active = selectedBaremos.has(item.scoring_config_id);
                    return (
                      <label
                        key={item.scoring_config_id}
                        className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition-colors ${
                          active
                            ? "border-amber bg-amber/5 ring-1 ring-amber/30"
                            : "border-border hover:border-amber/40"
                        }`}
                      >
                        <input
                          type="checkbox"
                          className="h-4 w-4 shrink-0 accent-amber"
                          checked={active}
                          onChange={() => toggleBaremo(item.scoring_config_id)}
                        />
                        <span className="text-sm text-dark">{item.variable_label}</span>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>

            {errorMessage ? <p className="text-sm text-danger">{errorMessage}</p> : null}
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-border px-5 py-4">
            <button type="button" className="colmena-button-secondary" onClick={onClose} disabled={isExporting}>
              Cancelar
            </button>
            <button
              type="button"
              className="colmena-button-primary inline-flex items-center justify-center"
              onClick={handleExport}
              disabled={isExporting || totalCount === 0}
            >
              {isExporting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              {isExporting ? "Generando ZIP..." : `Exportar (${totalCount})`}
            </button>
          </div>
        </div>
      </div>

      {captureSpecs ? (
        <div style={{ position: "fixed", left: -10000, top: 0, pointerEvents: "none" }} aria-hidden="true">
          {captureSpecs.map((spec, index) => (
            <div key={index} style={{ width: 640, height: 420 }}>
              {spec.kind === "reliability" ? (
                <AlphaBarChart
                  formId={formId}
                  variableTargets={spec.variableTargets}
                  dimensionTargets={spec.dimensionTargets}
                  exportMode
                  onChartReady={(chart) => handleChartReady(index, spec, chart)}
                />
              ) : null}
              {spec.kind === "normality" ? (
                <NormalityHistogramCard
                  formId={formId}
                  result={spec.result}
                  exportMode
                  onChartReady={(chart) => handleChartReady(index, spec, chart)}
                />
              ) : null}
              {spec.kind === "correlation" ? (
                <CorrelationScatterChart
                  formId={formId}
                  xLabel={spec.cell.row_label}
                  yLabel={spec.cell.column_label}
                  xValues={spec.xValues}
                  yValues={spec.yValues}
                  coefficient={spec.coefficient}
                  pValue={spec.pValue}
                  method={spec.methodUsed}
                  alpha={spec.alpha}
                  exportMode
                  onChartReady={(chart) => handleChartReady(index, spec, chart)}
                />
              ) : null}
              {spec.kind === "baremo" ? (
                <BaremoLevelsChart
                  formId={formId}
                  chartKey={spec.item.scoring_config_id}
                  variableLabel={spec.item.variable_label}
                  levels={spec.item.levels}
                  exportMode
                  onChartReady={(chart) => handleChartReady(index, spec, chart)}
                />
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </>
  );
}
