import { StudyStageCard } from "./StudyStageCard";

export function VariableBuilder({ href, summary, status }: { href: string; summary: string; status: "pending" | "in_progress" | "complete" }) {
  return <StudyStageCard actionLabel="Definir variable" href={href} status={status} summary={summary} title="Variable principal" />;
}
