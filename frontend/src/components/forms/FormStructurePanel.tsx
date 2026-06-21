export function FormStructurePanel() {
  const sections = [
    { title: "Sección 1", name: "Datos generales", count: 3 },
    { title: "Sección 2", name: "Escala principal", count: 8 },
    { title: "Sección 3", name: "Comentarios finales", count: 1 },
  ];

  return (
    <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <h3 className="text-base font-semibold text-dark">Estructura del formulario</h3>
      <p className="mt-1 text-sm text-muted">Organiza tus preguntas por sección.</p>
      <div className="mt-4 space-y-3">
        {sections.map((section) => (
          <div className="rounded-[18px] border border-border px-4 py-4" key={section.title}>
            <p className="text-sm text-muted">{section.title}</p>
            <div className="mt-2 flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-dark">{section.name}</p>
              <span className="rounded-full bg-turquoiseSoft px-3 py-1 text-xs font-medium text-turquoiseDark">
                {section.count} preguntas
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
