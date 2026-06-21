export function StudyReviewPanel({ items }: { items: string[] }) {
  return (
    <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <h3 className="text-base font-semibold text-dark">Revisión de la estructura</h3>
      <ul className="mt-4 space-y-3 text-sm text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
