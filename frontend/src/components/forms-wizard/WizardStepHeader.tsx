export function WizardStepHeader({
  step,
  title,
  description,
}: {
  step: string;
  title: string;
  description: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber">{step}</p>
      <h2 className="text-2xl font-semibold tracking-tight text-graphite">{title}</h2>
      <p className="max-w-3xl text-sm leading-7 text-muted">{description}</p>
    </div>
  );
}
