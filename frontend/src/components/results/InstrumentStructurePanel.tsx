type DimensionSummary = {
  name: string;
  items: number;
  color?: string;
};

const defaultDimensions: DimensionSummary[] = [
  { name: "Calidad del servicio", items: 5, color: "bg-[#356DFF]" },
  { name: "Atención al cliente", items: 4, color: "bg-turquoise" },
  { name: "Experiencia de uso", items: 5, color: "bg-amber" },
];

export function InstrumentStructurePanel({
  variableName = "Variable principal",
  scoreLabel = "Score total",
  dimensions = defaultDimensions,
}: {
  variableName?: string;
  scoreLabel?: string;
  dimensions?: DimensionSummary[];
}) {
  return (
    <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <h3 className="text-base font-semibold text-dark">Estructura del instrumento</h3>
      <div className="mt-5 space-y-4 border-l border-border pl-4">
        <div>
          <p className="text-sm text-muted">Variable: {variableName}</p>
          <p className="text-sm text-[#4F63FF]">({scoreLabel})</p>
        </div>
        {dimensions.map((dimension) => (
          <div className="flex items-center justify-between gap-3" key={dimension.name}>
            <div className="flex items-center gap-3">
              <span className={`h-3 w-3 rounded-full ${dimension.color ?? "bg-turquoise"}`} />
              <span className="text-sm text-dark">{dimension.name}</span>
            </div>
            <span className="text-sm text-muted">{dimension.items} ítems</span>
          </div>
        ))}
      </div>
    </div>
  );
}
