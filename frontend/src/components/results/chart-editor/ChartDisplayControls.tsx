export function ChartDisplayControls({
  showPercentages,
  showFrequencies,
  showValues,
  showLegend,
  showDataTable,
  showAdvancedJson,
  onToggle,
}: {
  showPercentages: boolean;
  showFrequencies: boolean;
  showValues: boolean;
  showLegend: boolean;
  showDataTable: boolean;
  showAdvancedJson: boolean;
  onToggle: (
    field:
      | "showPercentages"
      | "showFrequencies"
      | "showValues"
      | "showLegend"
      | "showDataTable"
      | "showAdvancedJson",
    value: boolean,
  ) => void;
}) {
  const items = [
    { key: "showPercentages", label: "Mostrar porcentajes", value: showPercentages },
    { key: "showFrequencies", label: "Mostrar frecuencias", value: showFrequencies },
    { key: "showValues", label: "Mostrar valores", value: showValues },
    { key: "showLegend", label: "Mostrar leyenda", value: showLegend },
    { key: "showDataTable", label: "Mostrar tabla de datos", value: showDataTable },
    { key: "showAdvancedJson", label: "Ver configuracion tecnica", value: showAdvancedJson },
  ] as const;

  return (
    <div className="space-y-3 rounded-2xl border border-border bg-[#fcfbf7] p-4">
      <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Leyenda y valores</h4>
      <div className="grid gap-3">
        {items.map((item) => (
          <label className="flex items-center gap-3 text-sm text-dark" key={item.key}>
            <input
              checked={item.value}
              className="h-4 w-4 accent-amber"
              onChange={(event) => onToggle(item.key, event.target.checked)}
              type="checkbox"
            />
            {item.label}
          </label>
        ))}
      </div>
    </div>
  );
}
