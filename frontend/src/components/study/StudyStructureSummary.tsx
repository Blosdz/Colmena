export function StudyStructureSummary({
  items,
}: {
  items: { label: string; value: string | number }[];
}) {
  return (
    <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <h3 className="text-base font-semibold text-dark">Estructura del estudio</h3>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <div className="rounded-[18px] border border-border px-4 py-4" key={item.label}>
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">{item.label}</p>
            <p className="mt-2 text-2xl font-semibold text-dark">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
