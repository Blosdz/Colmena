import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { generateApaBatch } from "../../api/apaTables";
import type { ApaTableBatch } from "../../types/apaTable";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Table, TableContainer, Td, Th } from "../ui/Table";

export function ApaTableViewer({ formId }: { formId: string }) {
  const [batch, setBatch] = useState<ApaTableBatch | null>(null);
  const mutation = useMutation({
    mutationFn: () =>
      generateApaBatch(formId, {
        form_id: formId,
        table_types: ["frequencies", "descriptives", "normality"],
        decimals: 3,
        include_discarded: false,
        score_aggregation: "mean",
      }),
    onSuccess: setBatch,
  });

  useEffect(() => {
    mutation.mutate();
  }, []);

  if (mutation.isPending && !batch) {
    return <LoadingState label="Generando tablas APA..." />;
  }

  if (mutation.isError && !batch) {
    return <ErrorState message={(mutation.error as Error).message} />;
  }

  if (!batch || batch.tables.length === 0) {
    return (
      <EmptyState
        title="No hay tablas APA disponibles"
        description="Cuando el formulario tenga resultados suficientes, aqui apareceran tablas preparadas para Word y revision academica."
      >
        <Button onClick={() => mutation.mutate()} variant="secondary">
          Reintentar
        </Button>
      </EmptyState>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">Se generaron {batch.total_tables} tablas base en formato APA 7.</p>
        <Button onClick={() => mutation.mutate()} variant="secondary">
          Refrescar tablas
        </Button>
      </div>
      {batch.tables.map((table) => (
        <Card className="space-y-4" key={table.table_id}>
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber">{table.table_type}</p>
            <h3 className="text-lg font-semibold text-dark">{table.title}</h3>
            {table.subtitle ? <p className="text-sm text-muted">{table.subtitle}</p> : null}
          </div>
          <TableContainer>
            <Table>
              <thead>
                <tr>
                  {table.columns.map((column) => (
                    <Th key={column.key}>{column.label}</Th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, index) => (
                  <tr key={`${table.table_id}-${index}`}>
                    {row.cells.map((cell, cellIndex) => (
                      <Td key={`${table.table_id}-${index}-${cellIndex}`}>{cell.value || "—"}</Td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </Table>
          </TableContainer>
          {table.notes.length > 0 ? (
            <div className="space-y-1 text-sm text-muted">
              {table.notes.map((note, index) => (
                <p key={`${table.table_id}-note-${index}`}>Nota. {note.text}</p>
              ))}
            </div>
          ) : null}
          <details className="rounded-2xl border border-border bg-[#fcfbf7] p-4">
            <summary className="cursor-pointer text-sm font-medium text-dark">Ver Markdown</summary>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-muted">{table.markdown}</pre>
          </details>
        </Card>
      ))}
    </div>
  );
}
