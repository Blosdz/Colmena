import { StudyStageCard } from "./StudyStageCard";

export function ScaleBuilder({ href, summary, status }: { href: string; summary: string; status: "pending" | "in_progress" | "complete" }) {
  return <StudyStageCard actionLabel="Configurar escala" href={href} status={status} summary={summary} title="Escala de respuesta" />;
}
