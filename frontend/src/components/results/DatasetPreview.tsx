import { useQuery } from "@tanstack/react-query";

import { getDatasetPreview } from "../../api/datasets";
import type { DatasetColumn } from "../../types/dataset";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Table, TableContainer, Td, Th } from "../ui/Table";

function renderCellValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

export function DatasetPreview({ formId }: { formId: string }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dataset-preview", formId],
    queryFn: () => getDatasetPreview(formId),
  });

  if (isLoading) {
    return <LoadingState label="Cargando preview del dataset..." />;
  }

  if (isError) {
    return <ErrorState message={(error as Error).message} />;
  }

  if (!data || data.rows.length === 0) {
    return (
      <EmptyState
        title="Aun no hay respuestas para este formulario"
        description="Primero publica el formulario y recolecta datos para visualizar la base tabular."
      />
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted">
        Mostrando {data.rows.length} filas de un total de {data.total_rows} respuestas y {data.total_columns} columnas.
      </p>
      <TableContainer>
        <Table>
          <thead>
            <tr>
              {data.columns.map((column: DatasetColumn) => (
                <Th key={column.name}>{column.label || column.name}</Th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, index) => (
              <tr key={`dataset-row-${index}`}>
                {data.columns.map((column) => (
                  <Td key={`${index}-${column.name}`} className="max-w-[220px] truncate">
                    {renderCellValue(row[column.name])}
                  </Td>
                ))}
              </tr>
            ))}
          </tbody>
        </Table>
      </TableContainer>
    </div>
  );
}
