import { StudyStageCard } from "./StudyStageCard";

export function InstrumentBuilder({ href, summary, status }: { href: string; summary: string; status: "pending" | "in_progress" | "complete" }) {
  return <StudyStageCard actionLabel="Crear instrumento" href={href} status={status} summary={summary} title="Instrumento" />;
}
