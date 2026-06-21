import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { GlassCard } from "../ui/GlassCard";
import { StatusPill } from "../ui/StatusPill";

export function ModuleProgressCard({
  title,
  description,
  status,
  href,
}: {
  title: string;
  description: string;
  status: string;
  href?: string;
}) {
  return (
    <GlassCard className="space-y-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1.5">
          <h3 className="text-base font-semibold text-dark">{title}</h3>
          <p className="text-sm leading-6 text-muted">{description}</p>
        </div>
        <StatusPill label={status} tone={status === "Listo" ? "published" : status === "Pendiente" ? "draft" : "results"} />
      </div>
      {href ? (
        <Link className="inline-flex items-center gap-2 text-sm font-medium text-info" to={href}>
          Continuar <ArrowRight className="h-4 w-4" />
        </Link>
      ) : null}
    </GlassCard>
  );
}
