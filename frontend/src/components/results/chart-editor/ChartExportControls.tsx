import { useState } from "react";

import type { ChartSpec } from "../../../types/chart";
import type { EditableChartState } from "../../../types/chartEditor";
import { Button } from "../../ui/Button";
import { Card } from "../../ui/Card";
import { buildChartImageFileName, downloadDataUrl, exportPlotlyToPng, exportPlotlyToSvg } from "./chartImageExport";
import { saveChartImageForWord } from "./chartImageUpload";

type ExportState = "idle" | "exporting" | "uploading" | "success" | "error";

export function ChartExportControls({
  chart,
  formId,
  graphDiv,
  state,
  onImageSaved,
}: {
  chart: ChartSpec;
  formId: string;
  graphDiv: unknown;
  state: EditableChartState;
  onImageSaved?: () => void;
}) {
  const [exportState, setExportState] = useState<ExportState>("idle");
  const [message, setMessage] = useState("");
  const [savedArtifactId, setSavedArtifactId] = useState<string | null>(null);

  const withGraphGuard = async (task: () => Promise<void>) => {
    if (!graphDiv) {
      setExportState("error");
      setMessage("El grafico aun no esta listo para exportacion.");
      return;
    }
    await task();
  };

  const handleDownloadPng = async () =>
    withGraphGuard(async () => {
      try {
        setExportState("exporting");
        const dataUrl = await exportPlotlyToPng(graphDiv);
        downloadDataUrl(dataUrl, buildChartImageFileName(chart, state, "png"));
        setExportState("success");
        setMessage("PNG generado correctamente.");
      } catch {
        setExportState("error");
        setMessage("No se pudo exportar el grafico.");
      }
    });

  const handleDownloadSvg = async () =>
    withGraphGuard(async () => {
      try {
        setExportState("exporting");
        const dataUrl = await exportPlotlyToSvg(graphDiv);
        downloadDataUrl(dataUrl, buildChartImageFileName(chart, state, "svg"));
        setExportState("success");
        setMessage("SVG generado correctamente.");
      } catch {
        setExportState("error");
        setMessage("No se pudo exportar el grafico.");
      }
    });

  const handleSave = async (format: "png" | "svg") =>
    withGraphGuard(async () => {
      try {
        setExportState("uploading");
        const dataUrl = format === "png" ? await exportPlotlyToPng(graphDiv) : await exportPlotlyToSvg(graphDiv);
        const response = await saveChartImageForWord({ formId, chart, state, dataUrl, format });
        setSavedArtifactId(response.image.artifact_id);
        setExportState("success");
        setMessage(format === "png" ? "Imagen guardada para el informe Word." : "SVG guardado, pero Word usara PNG.");
        onImageSaved?.();
      } catch (error) {
        setExportState("error");
        setMessage(error instanceof Error ? error.message : "No se pudo guardar la imagen.");
      }
    });

  const handleCopyJson = async () => {
    if (!navigator.clipboard) {
      return;
    }
    await navigator.clipboard.writeText(JSON.stringify({ chart, editable_state: state }, null, 2));
    setExportState("success");
    setMessage("Configuracion JSON copiada.");
  };

  return (
    <Card className="space-y-4 p-4">
      <div className="space-y-1">
        <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Exportacion</h4>
        <p className="text-sm text-muted">Genera una imagen del grafico actual o guardala como recurso reutilizable para Word.</p>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        <Button loading={exportState === "exporting"} onClick={() => void handleDownloadPng()} variant="secondary">
          Descargar PNG
        </Button>
        <Button loading={exportState === "exporting"} onClick={() => void handleDownloadSvg()} variant="secondary">
          Descargar SVG
        </Button>
        <Button loading={exportState === "uploading"} onClick={() => void handleSave("png")}>
          Guardar PNG para Word
        </Button>
        <Button loading={exportState === "uploading"} onClick={() => void handleSave("svg")} variant="secondary">
          Guardar SVG como recurso
        </Button>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={() => void handleCopyJson()} size="sm" variant="ghost">
          Copiar configuracion JSON
        </Button>
        {savedArtifactId ? <p className="text-xs text-success">Disponible para Word: {savedArtifactId}</p> : null}
      </div>
      {message ? (
        <p
          className={`text-sm ${
            exportState === "error" ? "text-danger" : exportState === "success" ? "text-success" : "text-muted"
          }`}
        >
          {message}
        </p>
      ) : null}
    </Card>
  );
}
