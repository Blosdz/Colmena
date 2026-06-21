import { Badge } from "../ui/Badge";

const toneByStatus: Record<string, "neutral" | "success" | "warning" | "danger" | "info"> = {
  draft: "warning",
  published: "success",
  collecting: "success",
  closed: "danger",
};

export function FormStatusBadge({ status }: { status: string }) {
  return <Badge tone={toneByStatus[status] ?? "neutral"}>{status}</Badge>;
}
