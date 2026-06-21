import { StudyStageCard } from "./StudyStageCard";

export function DimensionBuilder({ href, summary, status }: { href: string; summary: string; status: "pending" | "in_progress" | "complete" }) {
  return <StudyStageCard actionLabel="Agregar dimensiones" href={href} status={status} summary={summary} title="Dimensiones" />;
}
