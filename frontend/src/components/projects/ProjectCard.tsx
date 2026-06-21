import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import type { Project } from "../../types/project";

function getProjectStatusLabel(status: string) {
  switch (status.toLowerCase()) {
    case "active":
      return "Activo";
    case "draft":
      return "Borrador";
    default:
      return status;
  }
}

function buildSecondaryLine(project: Project) {
  const parts = [project.institution, project.career].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : null;
}

export function ProjectCard({
  project,
  actionLabel = "Abrir estudio",
  href,
}: {
  project: Project;
  actionLabel?: string;
  href?: string;
}) {
  const secondaryLine = buildSecondaryLine(project);

  return (
    <div className="flex min-h-[170px] flex-col rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <h3 className="line-clamp-2 text-[17px] font-semibold leading-7 text-dark">{project.title}</h3>
          {secondaryLine ? <p className="text-sm text-muted">{secondaryLine}</p> : null}
        </div>
        <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-dark">
          {getProjectStatusLabel(project.status)}
        </span>
      </div>

      <Link
        className="mt-auto inline-flex h-11 items-center justify-center gap-2 rounded-[18px] border border-border text-sm font-medium text-dark transition hover:bg-[#FBF7EE]"
        to={href || `/projects/${project.id}`}
      >
        {actionLabel}
        <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );
}
