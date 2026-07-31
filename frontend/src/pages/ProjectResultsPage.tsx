import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardList, Plus } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import {
  deleteBaremoTable,
  listBaremoTables,
  upsertBaremoTable,
  type BaremoGroupKind,
  type BaremoTableRow,
  type BaremoTableSavePayload,
} from "../api/baremoTables";
import { listProjectForms } from "../api/forms";
import { getProject } from "../api/projects";
import { getBaremoResolution } from "../api/scoring";
import { PageHeader } from "../components/layout/PageHeader";
import { BaremoResultTable } from "../components/results/BaremoResultTable";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { LoadingState } from "../components/ui/LoadingState";
import type { VariableBaremo } from "../types/scoring";

const AUTOSAVE_DEBOUNCE_MS = 800;
const DEFAULT_CUSTOM_ROWS: BaremoTableRow[] = [
  { category: "Bajo", frequency: 0 },
  { category: "Medio", frequency: 0 },
  { category: "Alto", frequency: 0 },
];

function getPrimaryForm<T extends { status: string }>(forms: T[]) {
  return forms.find((form) => form.status === "published") ?? forms[0] ?? null;
}

interface EditableTable {
  tableKey: string;
  groupKind: BaremoGroupKind;
  title: string;
  rows: BaremoTableRow[];
  /** Filas calculadas de las respuestas (solo tablas derivadas): para "Restablecer". */
  computedRows: BaremoTableRow[] | null;
}

function computedRowsFromResolution(item: VariableBaremo): BaremoTableRow[] {
  return item.levels.map((level) => ({ category: level.label, frequency: level.n }));
}

/** Los configs de nivel "instrument" o "project_variable" representan la variable completa. */
function groupKindForScoringLevel(scoringLevel: string): BaremoGroupKind {
  return scoringLevel === "dimension" ? "dimension" : "variable";
}

export function ProjectResultsPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);
  const queryClient = useQueryClient();

  const projectQuery = useQuery({
    queryKey: ["project-results-project", projectId],
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });
  const formsQuery = useQuery({
    queryKey: ["project-results-forms", projectId],
    queryFn: () => listProjectForms(projectId),
    enabled: Boolean(projectId),
  });

  const primaryForm = getPrimaryForm(formsQuery.data?.items ?? []);
  const formId = primaryForm?.id ?? "";

  const resolutionQuery = useQuery({
    queryKey: ["project-results-baremo-resolution", formId],
    queryFn: () => getBaremoResolution(formId),
    enabled: Boolean(formId),
  });
  const savedQuery = useQuery({
    queryKey: ["project-results-baremo-tables", formId],
    queryFn: () => listBaremoTables(formId),
    enabled: Boolean(formId),
  });

  // Estado local editable: se inicializa mezclando la resolución automática con
  // lo guardado; después de eso el usuario manda y solo se persiste hacia el backend.
  const [tables, setTables] = useState<EditableTable[] | null>(null);

  const mergedTables = useMemo(() => {
    if (!resolutionQuery.data || !savedQuery.data) return null;
    const savedByKey = new Map(savedQuery.data.items.map((item) => [item.table_key, item]));
    const result: EditableTable[] = [];

    for (const item of resolutionQuery.data.items) {
      const computedRows = computedRowsFromResolution(item);
      const saved = savedByKey.get(item.scoring_config_id);
      savedByKey.delete(item.scoring_config_id);
      result.push({
        tableKey: item.scoring_config_id,
        groupKind: groupKindForScoringLevel(item.scoring_level),
        title: saved?.title ?? item.variable_label,
        rows: saved?.rows ?? computedRows,
        computedRows,
      });
    }

    // Tablas guardadas sin config asociado (custom o de configs eliminados).
    for (const saved of savedByKey.values()) {
      result.push({
        tableKey: saved.table_key,
        groupKind: saved.group_kind,
        title: saved.title,
        rows: saved.rows,
        computedRows: null,
      });
    }
    return result;
  }, [resolutionQuery.data, savedQuery.data]);

  useEffect(() => {
    if (mergedTables && tables === null) {
      setTables(mergedTables);
    }
  }, [mergedTables, tables]);

  const saveMutation = useMutation({
    mutationFn: ({ tableKey, payload }: { tableKey: string; payload: BaremoTableSavePayload }) =>
      upsertBaremoTable(formId, tableKey, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-results-baremo-tables", formId] });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: (tableKey: string) => deleteBaremoTable(formId, tableKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-results-baremo-tables", formId] });
    },
  });

  // Autosave con debounce: guarda cada tabla editada sin bloquear la escritura.
  const saveTimers = useRef(new Map<string, ReturnType<typeof setTimeout>>());
  const scheduleSave = (table: EditableTable) => {
    const existing = saveTimers.current.get(table.tableKey);
    if (existing) clearTimeout(existing);
    saveTimers.current.set(
      table.tableKey,
      setTimeout(() => {
        saveTimers.current.delete(table.tableKey);
        saveMutation.mutate({
          tableKey: table.tableKey,
          payload: {
            title: table.title.trim() || "Sin título",
            group_kind: table.groupKind,
            rows: table.rows,
          },
        });
      }, AUTOSAVE_DEBOUNCE_MS),
    );
  };
  useEffect(() => {
    const timers = saveTimers.current;
    return () => {
      for (const timer of timers.values()) clearTimeout(timer);
    };
  }, []);

  const updateTable = (tableKey: string, patch: Partial<Pick<EditableTable, "title" | "rows">>) => {
    setTables((current) => {
      if (!current) return current;
      return current.map((table) => {
        if (table.tableKey !== tableKey) return table;
        const updated = { ...table, ...patch };
        scheduleSave(updated);
        return updated;
      });
    });
  };

  const resetTable = (tableKey: string) => {
    setTables((current) => {
      if (!current) return current;
      return current.map((table) => {
        if (table.tableKey !== tableKey || !table.computedRows) return table;
        const updated = { ...table, rows: table.computedRows };
        scheduleSave(updated);
        return updated;
      });
    });
  };

  const addCustomTable = (groupKind: BaremoGroupKind) => {
    const tableKey = crypto.randomUUID();
    const title = groupKind === "dimension" ? "Nueva dimensión" : "Nueva variable";
    const table: EditableTable = {
      tableKey,
      groupKind,
      title,
      rows: DEFAULT_CUSTOM_ROWS.map((row) => ({ ...row })),
      computedRows: null,
    };
    setTables((current) => [...(current ?? []), table]);
    saveMutation.mutate({
      tableKey,
      payload: { title, group_kind: groupKind, rows: table.rows },
    });
  };

  const removeTable = (table: EditableTable) => {
    if (!window.confirm(`¿Eliminar la tabla "${table.title}"?`)) return;
    const timer = saveTimers.current.get(table.tableKey);
    if (timer) {
      clearTimeout(timer);
      saveTimers.current.delete(table.tableKey);
    }
    setTables((current) => (current ? current.filter((t) => t.tableKey !== table.tableKey) : current));
    deleteMutation.mutate(table.tableKey);
  };

  if (projectQuery.isLoading || formsQuery.isLoading) {
    return <LoadingState label="Cargando resultados..." />;
  }

  if (projectQuery.isError || formsQuery.isError || !projectQuery.data || !primaryForm) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader
          title="Resultados"
          description="Tablas de baremos por variable y por dimensión."
        />
        <div className="mt-6 flex flex-1 flex-col items-center justify-center rounded-[24px] border border-dashed border-border bg-white px-6 py-16 text-center shadow-card">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber/10 text-amber">
            <ClipboardList className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold text-dark">Aún no hay formulario</h3>
          <p className="mt-2 max-w-md text-sm text-muted">
            Crea el instrumento del proyecto para poder construir sus tablas de baremos.
          </p>
          <Link className="colmena-button-primary mt-5 inline-flex items-center" to={`/project/${projectId}`}>
            Ir al constructor
          </Link>
        </div>
      </div>
    );
  }

  if (resolutionQuery.isLoading || savedQuery.isLoading || tables === null) {
    return <LoadingState label="Cargando tablas de baremos..." />;
  }

  const variableTables = tables.filter((table) => table.groupKind !== "dimension");
  const dimensionTables = tables.filter((table) => table.groupKind === "dimension");

  const renderSection = (
    sectionTitle: string,
    sectionDescription: string,
    sectionTables: EditableTable[],
    customKind: BaremoGroupKind,
  ) => (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-dark">{sectionTitle}</h2>
          <p className="text-sm text-muted">{sectionDescription}</p>
        </div>
        <button
          className="colmena-button-secondary inline-flex items-center text-sm"
          onClick={() => addCustomTable(customKind)}
          type="button"
        >
          <Plus className="mr-1.5 h-4 w-4" />
          {customKind === "dimension" ? "Agregar dimensión" : "Agregar variable"}
        </button>
      </div>
      {sectionTables.length === 0 ? (
        <div className="rounded-[18px] border border-dashed border-border bg-white px-4 py-8 text-center text-sm text-muted shadow-card">
          No hay tablas en esta sección todavía.
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {sectionTables.map((table) => (
            <BaremoResultTable
              key={table.tableKey}
              title={table.title}
              rows={table.rows}
              onTitleChange={(title) => updateTable(table.tableKey, { title })}
              onRowsChange={(rows) => updateTable(table.tableKey, { rows })}
              onDelete={table.computedRows ? undefined : () => removeTable(table)}
              onReset={table.computedRows ? () => resetTable(table.tableKey) : undefined}
            />
          ))}
        </div>
      )}
    </section>
  );

  return (
    <div className="space-y-8">
      <PageHeader
        title="Resultados"
        description="Tablas de baremos con frecuencias editables; el porcentaje se recalcula automáticamente."
      />
      {renderSection(
        "Por variable",
        "Una tabla por cada variable de estudio.",
        variableTables,
        "variable",
      )}
      {renderSection(
        "Por dimensión",
        "Una tabla por cada dimensión de los instrumentos.",
        dimensionTables,
        "dimension",
      )}
    </div>
  );
}
