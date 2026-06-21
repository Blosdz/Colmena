import { StepBadge } from "../ui/StepBadge";

export type WorkspaceStep = {
  key: string;
  label: string;
  done?: boolean;
};

export function WorkspaceStepper({
  steps,
  currentKey,
}: {
  steps: WorkspaceStep[];
  currentKey: string;
}) {
  const currentIndex = Math.max(
    0,
    steps.findIndex((step) => step.key === currentKey),
  );

  return (
    <div className="grid gap-2.5 md:grid-cols-2 xl:grid-cols-5">
      {steps.map((step, index) => (
        <div className="rounded-[20px] border border-border bg-white/70 px-4 py-3 backdrop-blur-sm" key={step.key}>
          <StepBadge index={index + 1} active={index === currentIndex} done={step.done || index < currentIndex} label={step.label} />
        </div>
      ))}
    </div>
  );
}
