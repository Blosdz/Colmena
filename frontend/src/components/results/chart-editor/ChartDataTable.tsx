import type { ChartDataTableModel } from "../../../types/chartEditor";
import { formatChartValue } from "../../../utils/chartFormatters";
import { EmptyState } from "../../ui/EmptyState";
import { Table, TableContainer, Td, Th } from "../../ui/Table";

export function ChartDataTable({ model }: { model: ChartDataTableModel | null }) {
  if (!model || model.rows.length === 0) {
    return (
      <EmptyState
        title="No hay tabla de datos disponible para este grafico"
        description="La especificacion visual no expone una tabla limpia reutilizable para esta vista."
      />
    );
  }

  const limitedRows = model.rows.slice(0, 50);

  return (
    <div className="space-y-3">
      <div>
        <h4 className="text-base font-semibold text-dark">Tabla de datos vinculada</h4>
        <p className="text-sm text-muted">
          Fuente: {model.sourceLabel}. Se muestran hasta 50 filas para mantener la lectura liviana.
        </p>
      </div>
      <TableContainer>
        <Table>
          <thead>
            <tr>
              {model.columns.map((column) => (
                <Th key={column}>{column}</Th>
              ))}
            </tr>
          </thead>
          <tbody>
            {limitedRows.map((row, index) => (
              <tr key={`chart-row-${index}`}>
                {model.columns.map((column) => (
                  <Td key={`${index}-${column}`}>{formatChartValue(row[column])}</Td>
                ))}
              </tr>
            ))}
          </tbody>
        </Table>
      </TableContainer>
    </div>
  );
}
