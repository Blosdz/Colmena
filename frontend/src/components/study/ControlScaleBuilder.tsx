import { StudyStageCard } from "./StudyStageCard";

export function ControlScaleBuilder({ href, summary, status }: { href: string; summary: string; status: "pending" | "in_progress" | "complete" }) {
  return <StudyStageCard actionLabel="Ajustar escala de control" href={href} status={status} summary={summary} title="Escala de control" />;
}
