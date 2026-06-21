import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import type { Form } from "../../types/form";
import { GlassCard } from "../ui/GlassCard";
import { FormStatusBadge } from "./FormStatusBadge";

export function FormCard({
  form,
  projectTitle,
  actionLabel = "Abrir formulario",
  href,
}: {
  form: Form;
  projectTitle?: string;
  actionLabel?: string;
  href?: string;
}) {
  return (
    <GlassCard className="flex h-full flex-col gap-4 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-dark">{form.title}</h3>
          {projectTitle ? <p className="text-sm text-muted">{projectTitle}</p> : null}
        </div>
        <FormStatusBadge status={form.status} />
      </div>

      <div className="mt-auto">
        <Link
          className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-2xl border border-border bg-white px-4 text-sm font-medium text-dark transition hover:bg-surfaceSoft"
          to={href || `/forms/${form.id}`}
        >
          {actionLabel} <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </GlassCard>
  );
}
