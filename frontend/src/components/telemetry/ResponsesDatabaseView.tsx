import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Database } from "lucide-react";

import { getDataDictionary, getResponsesDataset } from "../../api/datasets";
import type { DatasetColumn } from "../../types/dataset";
import { palette } from "../../utils/telemetryChart";
import { LoadingState } from "../ui/LoadingState";

const MAX_ROWS = 200;
const ANCHOR_COLUMN_ORDER = ["respondent_code", "response_status", "submitted_at"];
const ANCHOR_COLUMN_LABELS: Record<string, string> = {
  respondent_code: "Respondiente",
  response_status: "Estado",
  submitted_at: "Enviado",
};
const NO_DIMENSION_GROUP = "Sin dimensión";

function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

export type TelemetryFilterKind = "all" | "dimension" | "variable";

interface ResponsesDatabaseViewProps {
  formId: string;
  /** Filtro compartido con el selector de gráficas: acota las columnas mostradas. */
  filterKind?: TelemetryFilterKind;
  filterName?: string | null;
}

export function ResponsesDatabaseView({ formId, filterKind = "all", filterName = null }: ResponsesDatabaseViewProps) {
  const datasetQuery = useQuery({
    queryKey: ["project-telemetry-dataset", formId],
    queryFn: () => getResponsesDataset(formId),
    enabled: Boolean(formId),
  });
  const dictionaryQuery = useQuery({
    queryKey: ["project-telemetry-data-dictionary", formId],
    queryFn: () => getDataDictionary(formId),
    enabled: Boolean(formId),
  });

  const dictionaryByQuestionId = useMemo(() => {
    const map = new Map<string, { dimensionName: string; variableName: string | null }>();
    for (const item of dictionaryQuery.data?.items ?? []) {
      map.set(item.question_id, {
        dimensionName: item.dimension_name ?? NO_DIMENSION_GROUP,
        variableName: item.project_variable_name ?? null,
      });
    }
    return map;
  }, [dictionaryQuery.data]);

  const { anchorColumns, groups } = useMemo(() => {
    const columns = datasetQuery.data?.columns ?? [];
    const anchor = ANCHOR_COLUMN_ORDER.map((name) => columns.find((col) => col.name === name)).filter(
      (col): col is DatasetColumn => Boolean(col),
    );

    const questionColumns = columns.filter((column) => column.kind !== "metadata");
    const filtered = questionColumns.filter((column) => {
      if (filterKind === "all" || !filterName) return true;
      const meta = column.question_id ? dictionaryByQuestionId.get(column.question_id) : undefined;
      if (filterKind === "dimension") return meta?.dimensionName === filterName;
      return meta?.variableName === filterName;
    });

    const groupMap = new Map<string, DatasetColumn[]>();
    for (const column of filtered) {
      const meta = column.question_id ? dictionaryByQuestionId.get(column.question_id) : undefined;
      const groupName = meta?.dimensionName ?? NO_DIMENSION_GROUP;
      const bucket = groupMap.get(groupName) ?? [];
      bucket.push(column);
      groupMap.set(groupName, bucket);
    }
    return { anchorColumns: anchor, groups: groupMap };
  }, [datasetQuery.data, dictionaryByQuestionId, filterKind, filterName]);

  if (datasetQuery.isLoading || dictionaryQuery.isLoading) {
    return <LoadingState label="Cargando base de datos de respuestas..." />;
  }

  if (datasetQuery.isError || dictionaryQuery.isError) {
    return (
      <section className="rounded-[18px] border border-border bg-white px-4 py-6 text-center text-sm text-muted shadow-card">
        No se pudo cargar la base de datos de respuestas.
      </section>
    );
  }

  const rows = datasetQuery.data?.rows ?? [];
  const groupEntries = [...groups.entries()];
  const groupColors = palette(groupEntries.length);

  if (rows.length === 0) {
    return (
      <section className="flex flex-col items-center justify-center rounded-[24px] border border-dashed border-border bg-white px-6 py-16 text-center shadow-card">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber/10 text-amber">
          <Database className="h-8 w-8" />
        </div>
        <h3 className="text-lg font-semibold text-dark">Aún no hay respuestas</h3>
        <p className="mt-2 max-w-md text-sm text-muted">
          En cuanto tus participantes respondan el formulario, aquí verás cada respuesta agrupada por dimensión.
        </p>
      </section>
    );
  }

  if (groupEntries.length === 0) {
    return (
      <section className="flex flex-col items-center justify-center rounded-[24px] border border-dashed border-border bg-white px-6 py-12 text-center shadow-card">
        <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-amber/10 text-amber">
          <Database className="h-7 w-7" />
        </div>
        <h3 className="text-base font-semibold text-dark">Sin preguntas para este filtro</h3>
        <p className="mt-1 max-w-md text-sm text-muted">
          No hay preguntas asociadas a "{filterName}". Prueba con otra dimensión o variable.
        </p>
      </section>
    );
  }

  const displayedRows = rows.slice(0, MAX_ROWS);

  return (
    <section className="w-full overflow-hidden rounded-[18px] border border-border bg-white shadow-card">
      <div className="max-h-[480px] w-full overflow-auto">
        <table className="w-full min-w-max border-collapse text-[12px]">
          <thead>
            <tr className="h-9">
              {anchorColumns.map((col, index) => (
                <th
                  key={col.name}
                  rowSpan={2}
                  className="sticky top-0 z-30 border-b border-r border-border bg-surfaceSoft px-3 py-1.5 text-left align-bottom text-[10px] font-semibold uppercase tracking-[0.06em] text-muted whitespace-nowrap"
                  style={{ left: index * 130 }}
                >
                  {ANCHOR_COLUMN_LABELS[col.name] ?? col.label}
                </th>
              ))}
              {groupEntries.map(([groupName, columns], groupIndex) => (
                <th
                  key={groupName}
                  colSpan={columns.length}
                  className="sticky top-0 z-20 border-b border-l border-border bg-surfaceSoft px-3 py-1.5 text-left text-[10px] font-semibold uppercase tracking-[0.06em] text-dark whitespace-nowrap"
                >
                  <span className="inline-flex items-center gap-1.5">
                    <span
                      className="inline-block h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: groupColors[groupIndex] }}
                    />
                    {groupName}
                  </span>
                </th>
              ))}
            </tr>
            <tr className="h-9">
              {groupEntries.flatMap(([groupName, columns], groupIndex) =>
                columns.map((col, index) => (
                  <th
                    key={col.name}
                    className={`sticky top-9 z-10 border-b border-border px-3 py-1.5 text-left font-medium text-muted whitespace-nowrap ${
                      index === 0 ? "border-l" : ""
                    }`}
                    style={{ backgroundColor: `${groupColors[groupIndex]}14` }}
                    title={`${groupName} · ${col.label}`}
                  >
                    {col.label}
                  </th>
                ))
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {displayedRows.map((row, rowIndex) => (
              <tr key={rowIndex} className="group">
                {anchorColumns.map((col, index) => (
                  <td
                    key={col.name}
                    className="sticky z-[5] whitespace-nowrap border-r border-border bg-white px-3 py-1.5 text-dark group-hover:bg-amber/5"
                    style={{ left: index * 130 }}
                  >
                    {formatCell(row[col.name])}
                  </td>
                ))}
                {groupEntries.flatMap(([, columns]) =>
                  columns.map((col) => (
                    <td
                      key={col.name}
                      className="whitespace-nowrap px-3 py-1.5 text-dark group-hover:bg-amber/5"
                    >
                      {formatCell(row[col.name])}
                    </td>
                  ))
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > MAX_ROWS ? (
        <div className="border-t border-border bg-surfaceSoft px-3 py-1.5 text-[11px] text-muted">
          Mostrando {MAX_ROWS} de {rows.length} respuestas · exporta a Excel para ver el total.
        </div>
      ) : null}
    </section>
  );
}
