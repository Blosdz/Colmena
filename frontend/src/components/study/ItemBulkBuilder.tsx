import { StudyStageCard } from "./StudyStageCard";

export function ItemBulkBuilder({ href, summary, status }: { href: string; summary: string; status: "pending" | "in_progress" | "complete" }) {
  return <StudyStageCard actionLabel="Importar ítems" href={href} status={status} summary={summary} title="Ítems" />;
}
