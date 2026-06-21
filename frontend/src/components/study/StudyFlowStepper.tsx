import { cn } from "../../utils/cn";

export type StudyStepStatus = "pending" | "in_progress" | "complete";

export function StudyFlowStepper({
  steps,
  compact = false,
}: {
  steps: { label: string; status: StudyStepStatus }[];
  compact?: boolean;
}) {
  return (
    <div
      className={cn(
        "grid gap-3",
        compact ? "grid-cols-2 xl:grid-cols-7" : "md:grid-cols-3 xl:grid-cols-7",
      )}
    >
      {steps.map((step, index) => {
        const isComplete = step.status === "complete";
        const isCurrent = step.status === "in_progress";

        return (
          <div
            className={cn(
              "rounded-[18px] border px-4 py-3 text-sm",
              isComplete && "border-[#BFE9D0] bg-[#F2FBF5]",
              isCurrent && "border-[#F5B21A] bg-[#FFF8E8]",
              step.status === "pending" && "border-border bg-white",
            )}
            key={step.label}
          >
            <p
              className={cn(
                "text-xs font-semibold uppercase tracking-[0.08em]",
                isComplete && "text-success",
                isCurrent && "text-amber",
                step.status === "pending" && "text-muted",
              )}
            >
              {index + 1}
            </p>
            <p className="mt-2 font-medium text-dark">{step.label}</p>
          </div>
        );
      })}
    </div>
  );
}
