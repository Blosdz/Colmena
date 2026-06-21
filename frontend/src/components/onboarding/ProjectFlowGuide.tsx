const steps = ["Proyecto", "Formulario", "Publicación", "Recolección", "Resultados", "Informe"];

export function ProjectFlowGuide() {
  return (
    <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <h3 className="text-base font-semibold text-dark">Flujo</h3>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {steps.map((step, index) => (
          <div
            className="flex items-center gap-3 rounded-2xl border border-border bg-white px-3 py-3 text-sm text-dark"
            key={step}
          >
            <span className="text-sm font-semibold text-amber">{index + 1}</span>
            <span>{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
