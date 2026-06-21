import { StudyStageCard } from "./StudyStageCard";

export function BaremoBuilder({ href, summary, status }: { href: string; summary: string; status: "pending" | "in_progress" | "complete" }) {
  return <StudyStageCard actionLabel="Configurar baremos" href={href} status={status} summary={summary} title="Baremos" />;
}
