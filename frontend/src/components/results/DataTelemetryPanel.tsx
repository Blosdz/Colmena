export function DataTelemetryPanel({
  title = "Información de datos",
  items = [
    ["Periodo de recolección", "Sin definir"],
    ["Primera respuesta", "Sin respuestas"],
    ["Última respuesta", "Sin respuestas"],
    ["Total registros", "0"],
    ["Registros válidos", "0"],
  ],
  statusLabel,
}: {
  title?: string;
  items?: Array<[string, string]>;
  statusLabel?: string;
}) {
  return (
    <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-dark">{title}</h3>
        {statusLabel ? (
          <span className="rounded-full bg-[#F2FBF5] px-3 py-1 text-xs font-medium text-success">{statusLabel}</span>
        ) : null}
      </div>
      <div className="mt-4 space-y-3 text-sm">
        {items.map(([label, value]) => (
          <div className="flex items-center justify-between gap-3" key={label}>
            <span className="text-muted">{label}</span>
            <span className="text-right text-dark">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
