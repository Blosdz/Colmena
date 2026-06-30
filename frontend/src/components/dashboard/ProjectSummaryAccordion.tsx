import { BarChart3, CheckCheck, ChevronDown, ChevronUp, FileText, MessageSquare, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";

import type { Project } from "../../types/project";
import { formatDate, formatNumber } from "../../utils/formatters";
import { ProjectMetricCard } from "./ProjectMetricCard";

function deriveMetrics(project: Project) {
  const current = project.demographics?.sample_size_current ?? 0;
  const planned = project.demographics?.sample_size_planned ?? 0;
  const progress = planned > 0 ? Math.min(100, Math.round((current / planned) * 100)) : 0;
  return {
    responses: formatNumber(current, 0),
    progress: `${progress}%`,
    consistency: current > 0 ? "98%" : "0%",
    reports: current > 0 ? "1" : "0",
    completion: current > 0 ? "82%" : "0%",
  };
}

export function ProjectSummaryAccordion({
  project,
  defaultExpanded = false,
}: {
  project: Project;
  defaultExpanded?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(defaultExpanded);
  const metrics = useMemo(() => deriveMetrics(project), [project]);

  return (
    <div className="rounded-[28px] border border-border bg-white px-6 py-6 shadow-card">
      <button
        className="flex w-full items-center justify-between gap-4 text-left"
        onClick={() => setIsOpen((current) => !current)}
        type="button"
      >
        <div className="flex min-w-0 items-center gap-5">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-[#fff5dd] text-amber">
            <BarChart3 className="h-6 w-6" />
          </div>
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-4">
              <h3 className="text-[18px] font-semibold text-dark">{project.title}</h3>
              <span className="rounded-full bg-[#eaf9ef] px-4 py-1 text-sm font-medium text-success">
                {project.status === "active" ? "Activo" : project.status}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-5 text-sm text-muted">
              <span>{formatNumber(project.demographics?.sample_size_current ?? 0, 0)} respuestas</span>
              <span>Actualizado {formatDate(project.updated_at)}</span>
            </div>
          </div>
        </div>
        {isOpen ? <ChevronUp className="h-5 w-5 text-muted" /> : <ChevronDown className="h-5 w-5 text-muted" />}
      </button>

      {isOpen ? (
        <div className="mt-6 grid gap-4 xl:grid-cols-5">
          <ProjectMetricCard
            delta="↑ 12%"
            hint="vs. periodo anterior"
            icon={MessageSquare}
            title="Respuestas recibidas"
            toneClass="bg-turquoiseSoft text-turquoiseDark"
            value={metrics.responses}
          />
          <ProjectMetricCard
            delta="↑ 8%"
            hint="vs. periodo anterior"
            icon={BarChart3}
            title="Avance del estudio"
            toneClass="bg-[#ffe9dd] text-orange"
            value={metrics.progress}
          />
          <ProjectMetricCard
            delta="↑ 2%"
            hint="vs. periodo anterior"
            icon={ShieldCheck}
            title="Consistencia de datos"
            toneClass="bg-turquoiseSoft text-turquoiseDark"
            value={metrics.consistency}
          />
          <ProjectMetricCard
            delta="↑ 3%"
            hint="vs. periodo anterior"
            icon={FileText}
            title="Reportes generados"
            toneClass="bg-[#fff5dd] text-amber"
            value={metrics.reports}
          />
          <ProjectMetricCard
            delta="↑ 6%"
            hint="vs. periodo anterior"
            icon={CheckCheck}
            title="Tasa de finalizacion"
            toneClass="bg-[#f3f5fb] text-graphite"
            value={metrics.completion}
          />
        </div>
      ) : null}
    </div>
  );
}
