const steps = ["Proyecto", "Formulario", "Publicacion", "Recoleccion", "Resultados", "Informe"];

export function ProjectFlowSteps() {
  return (
    <div className="rounded-[24px] border border-border bg-white px-4 py-4 shadow-card">
      <h3 className="mb-4 text-base font-semibold text-dark">Flujo</h3>
      <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-2">
        {steps.map((step, index) => (
          <div className="flex items-center gap-3 rounded-2xl border border-border px-3 py-3 text-sm text-dark" key={step}>
            <span className="text-xs font-semibold text-amber">{index + 1}</span>
            <span>{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
