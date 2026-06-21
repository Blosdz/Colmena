export function BaremoSummaryPanel({
  name = "Baremo general",
  scaleLabel = "Escala no definida",
  configCount = 0,
}: {
  name?: string;
  scaleLabel?: string;
  configCount?: number;
}) {
  return (
    <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <h3 className="text-base font-semibold text-dark">Baremos</h3>
      <div className="mt-4 space-y-3 text-sm">
        <p className="text-muted">Configuraciones activas: {configCount}</p>
        <div className="flex items-center justify-between gap-3">
          <span className="text-dark">{name}</span>
          <span className="rounded-full bg-[#eaf9ef] px-3 py-1 text-xs font-medium text-success">Activo</span>
        </div>
        <p className="text-muted">{scaleLabel}</p>
      </div>
    </div>
  );
}
