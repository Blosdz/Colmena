import { Plus, RotateCcw, Trash2, X } from "lucide-react";

import type { BaremoTableRow } from "../../api/baremoTables";

interface BaremoResultTableProps {
  title: string;
  rows: BaremoTableRow[];
  onTitleChange: (title: string) => void;
  onRowsChange: (rows: BaremoTableRow[]) => void;
  /** Tablas custom se pueden eliminar; las derivadas solo restablecer. */
  onDelete?: () => void;
  onReset?: () => void;
}

function formatPercent(frequency: number, total: number): string {
  if (total <= 0) return "—";
  return `${((frequency / total) * 100).toFixed(1)} %`;
}

/**
 * Tabla de baremo con exactamente 3 columnas: Categoría | Frecuencia | Porcentaje.
 * El porcentaje nunca se edita: se deriva de las frecuencias en cada render.
 */
export function BaremoResultTable({
  title,
  rows,
  onTitleChange,
  onRowsChange,
  onDelete,
  onReset,
}: BaremoResultTableProps) {
  const total = rows.reduce((sum, row) => sum + (Number.isFinite(row.frequency) ? row.frequency : 0), 0);

  const updateRow = (index: number, patch: Partial<BaremoTableRow>) => {
    onRowsChange(rows.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  };

  const removeRow = (index: number) => {
    onRowsChange(rows.filter((_, i) => i !== index));
  };

  const addRow = () => {
    onRowsChange([...rows, { category: "", frequency: 0 }]);
  };

  return (
    <section className="overflow-hidden rounded-[18px] border border-border bg-white shadow-card">
      <div className="flex items-center gap-2 border-b border-border bg-surfaceSoft px-4 py-2.5">
        <input
          aria-label="Nombre de la tabla"
          className="colmena-input h-9 flex-1 !bg-transparent text-sm font-semibold"
          value={title}
          onChange={(event) => onTitleChange(event.target.value)}
        />
        {onReset ? (
          <button
            className="colmena-button-secondary inline-flex h-8 items-center px-2.5 text-xs"
            onClick={onReset}
            title="Restablecer a los valores calculados de las respuestas"
            type="button"
          >
            <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
            Restablecer
          </button>
        ) : null}
        {onDelete ? (
          <button
            className="colmena-button-secondary inline-flex h-8 items-center px-2.5 text-xs text-danger"
            onClick={onDelete}
            title="Eliminar esta tabla"
            type="button"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        ) : null}
      </div>

      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-surfaceSoft/60 text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">
            <th className="px-4 py-2">Categoría</th>
            <th className="w-36 px-4 py-2">Frecuencia</th>
            <th className="w-32 px-4 py-2">Porcentaje</th>
            <th className="w-10 px-2 py-2" aria-label="Acciones" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row, index) => (
            <tr key={index} className="group">
              <td className="px-4 py-1.5">
                <input
                  aria-label={`Categoría fila ${index + 1}`}
                  className="colmena-input h-8 w-full text-sm"
                  placeholder="Categoría"
                  value={row.category}
                  onChange={(event) => updateRow(index, { category: event.target.value })}
                />
              </td>
              <td className="px-4 py-1.5">
                <input
                  aria-label={`Frecuencia fila ${index + 1}`}
                  className="colmena-input h-8 w-full text-sm"
                  min={0}
                  type="number"
                  value={Number.isFinite(row.frequency) ? row.frequency : 0}
                  onChange={(event) => {
                    const parsed = Number(event.target.value);
                    updateRow(index, { frequency: Number.isFinite(parsed) && parsed >= 0 ? parsed : 0 });
                  }}
                />
              </td>
              <td className="px-4 py-1.5 font-medium tabular-nums text-dark">
                {formatPercent(row.frequency, total)}
              </td>
              <td className="px-2 py-1.5 text-center">
                <button
                  aria-label={`Eliminar fila ${index + 1}`}
                  className="rounded-md p-1 text-muted opacity-0 transition-opacity hover:bg-danger/10 hover:text-danger group-hover:opacity-100"
                  onClick={() => removeRow(index)}
                  type="button"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t border-border bg-surfaceSoft/60 text-sm font-semibold text-dark">
            <td className="px-4 py-2">Total</td>
            <td className="px-4 py-2 tabular-nums">{total}</td>
            <td className="px-4 py-2 tabular-nums">{total > 0 ? "100.0 %" : "—"}</td>
            <td className="px-2 py-2" />
          </tr>
        </tfoot>
      </table>

      <div className="border-t border-border px-4 py-2">
        <button
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted transition-colors hover:text-dark"
          onClick={addRow}
          type="button"
        >
          <Plus className="h-3.5 w-3.5" />
          Agregar fila
        </button>
      </div>
    </section>
  );
}
