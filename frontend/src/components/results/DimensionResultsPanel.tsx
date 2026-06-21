type DimensionResultRow = {
  name: string;
  mean: string;
  sd: string;
  level: string;
  color?: string;
  progress?: number;
};

const defaultRows: DimensionResultRow[] = [
  { name: "Calidad del servicio", mean: "4.21", sd: "0.74", level: "Alto", color: "bg-[#356DFF]", progress: 84 },
  { name: "Atención al cliente", mean: "4.05", sd: "0.81", level: "Alto", color: "bg-turquoise", progress: 76 },
  { name: "Experiencia de uso", mean: "3.68", sd: "0.92", level: "Medio", color: "bg-amber", progress: 68 },
];

export function DimensionResultsPanel({
  rows = defaultRows,
  note = "Escala: 1 = Muy bajo | 5 = Muy alto",
}: {
  rows?: DimensionResultRow[];
  note?: string;
}) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-[minmax(180px,1.5fr)_1fr_72px_72px_72px] gap-3 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
        <span>Resultados por dimensiones</span>
        <span />
        <span>Promedio</span>
        <span>DE</span>
        <span>Nivel</span>
      </div>
      <div className="space-y-5">
        {rows.map((dimension) => (
          <div className="grid grid-cols-[minmax(180px,1.5fr)_1fr_72px_72px_72px] items-center gap-3" key={dimension.name}>
            <div className="flex items-center gap-3">
              <span className={`h-3 w-3 rounded-full ${dimension.color ?? "bg-turquoise"}`} />
              <span className="text-sm text-dark">{dimension.name}</span>
            </div>
            <div className="h-2 rounded-full bg-[#F0F2F4]">
              <div
                className={`h-2 rounded-full ${dimension.color ?? "bg-turquoise"}`}
                style={{ width: `${Math.max(12, Math.min(100, dimension.progress ?? 0))}%` }}
              />
            </div>
            <span className="text-sm text-dark">{dimension.mean}</span>
            <span className="text-sm text-dark">{dimension.sd}</span>
            <span className="inline-flex w-fit rounded-full bg-[#EEF8ED] px-3 py-1 text-xs font-medium text-success">
              {dimension.level}
            </span>
          </div>
        ))}
      </div>
      <p className="text-sm text-muted">{note}</p>
    </div>
  );
}
