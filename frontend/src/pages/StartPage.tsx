import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BarChart3, FileText, ListChecks, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { listProjects } from "../api/projects";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";

const processSteps = [
  { num: "01", label: "Proyecto", desc: "Define contexto y objetivo" },
  { num: "02", label: "Variable", desc: "Qué vas a medir" },
  { num: "03", label: "Dimensiones", desc: "Estructura del constructo" },
  { num: "04", label: "Instrumento", desc: "Cuestionario o escala" },
  { num: "05", label: "Ítems", desc: "Preguntas del formulario" },
  { num: "06", label: "Escala", desc: "Tipo de respuesta" },
  { num: "07", label: "Baremos", desc: "Niveles de interpretación" },
  { num: "08", label: "Link", desc: "Publicar y recolectar" },
  { num: "09", label: "Respuestas", desc: "Base de datos en vivo" },
  { num: "10", label: "Resultados", desc: "Estadística calculada" },
  { num: "11", label: "Informe", desc: "Word, PDF y gráficos" },
];

const features = [
  {
    icon: ListChecks,
    title: "Constructor de formularios",
    desc: "Importa ítems desde Excel, configura escalas Likert y baremos en segundos.",
    color: "from-amber/20 to-amber/5",
    iconColor: "text-amber",
  },
  {
    icon: BarChart3,
    title: "Telemetría en tiempo real",
    desc: "Monitorea completitud, omisiones y calidad de tu base mientras llegan respuestas.",
    color: "from-turquoise/20 to-turquoise/5",
    iconColor: "text-turquoise",
  },
  {
    icon: Sparkles,
    title: "Análisis estadístico guiado",
    desc: "Descriptivos, normalidad, correlaciones y comparaciones sin escribir fórmulas.",
    color: "from-info/10 to-info/5",
    iconColor: "text-info",
  },
  {
    icon: FileText,
    title: "Reportes profesionales",
    desc: "Genera tablas APA, gráficos editables e informes Word listos para entregar.",
    color: "from-honey/15 to-honey/5",
    iconColor: "text-honey",
  },
];

export function StartPage() {
  const projectsQuery = useQuery({
    queryKey: ["start-projects"],
    queryFn: listProjects,
  });

  if (projectsQuery.isLoading) {
    return <LoadingState label="Preparando inicio..." />;
  }

  if (projectsQuery.isError) {
    return <ErrorState message={(projectsQuery.error as Error).message} />;
  }

  const projects = projectsQuery.data?.items ?? [];
  const latestProject = projects[0] ?? null;

  return (
    <div className="space-y-8 animate-colmena-fade-in">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-[24px] bg-gradient-to-br from-[#1a1a2e] via-[#16213e] to-[#0f3460] px-10 py-12 text-white">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(245,178,26,0.15),transparent_50%),radial-gradient(ellipse_at_bottom_right,rgba(17,183,178,0.12),transparent_50%)]" />
        <div className="relative z-10 max-w-2xl space-y-5">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-[12px] font-medium text-amber backdrop-blur-sm">
            <Sparkles className="h-3.5 w-3.5" />
            Línea de producción científica
          </div>
          <h1 className="text-[36px] font-bold leading-[1.15] tracking-tight">
            Construye resultados estadísticos
            <br />
            <span className="text-amber">desde tu formulario</span>
          </h1>
          <p className="text-[15px] leading-7 text-white/70">
            Colmena te guía desde el proyecto, la variable y el instrumento hasta las
            respuestas, las tablas, los gráficos y el informe final — todo en un solo flujo.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              className="inline-flex h-12 items-center gap-2 rounded-xl bg-amber px-6 text-[15px] font-semibold text-white shadow-lg shadow-amber/25 transition hover:bg-[#e5a310] hover:shadow-amber/35"
              to="/project/new"
            >
              Crear proyecto
              <ArrowRight className="h-4 w-4" />
            </Link>
            {latestProject && (
              <Link
                className="inline-flex h-12 items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-6 text-[15px] font-medium text-white backdrop-blur-sm transition hover:bg-white/10"
                to={`/project/${latestProject.id}`}
              >
                Continuar: {latestProject.title}
              </Link>
            )}
            {!latestProject && projects.length === 0 && (
              <Link
                className="inline-flex h-12 items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-6 text-[15px] font-medium text-white backdrop-blur-sm transition hover:bg-white/10"
                to="/archive/projects"
              >
                Ver archivo
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Process Pipeline */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-dark">Flujo metodológico</h2>
          <span className="text-xs font-medium text-muted">11 etapas</span>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-11">
          {processSteps.map((step) => (
            <div
              className="group flex flex-col items-center gap-1.5 rounded-2xl border border-[#eef0f3] bg-white px-3 py-4 text-center transition hover:border-amber/30 hover:shadow-sm"
              key={step.num}
            >
              <span className="text-[10px] font-bold text-amber/60">{step.num}</span>
              <span className="text-[12px] font-semibold text-dark leading-tight">
                {step.label}
              </span>
              <span className="text-[10px] text-muted leading-tight hidden xl:block">
                {step.desc}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {features.map((f) => (
          <div
            className={`rounded-2xl bg-gradient-to-br ${f.color} border border-[#eef0f3] p-5 transition hover:shadow-soft`}
            key={f.title}
          >
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-white/80 ${f.iconColor} shadow-sm`}>
              <f.icon className="h-5 w-5" />
            </div>
            <h3 className="mt-4 text-[15px] font-semibold text-dark">{f.title}</h3>
            <p className="mt-2 text-[13px] leading-6 text-muted">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Recent projects */}
      {projects.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-dark">Proyectos recientes</h2>
            <Link
              className="text-[13px] font-medium text-amber hover:underline"
              to="/archive/projects"
            >
              Ver todos →
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {projects.slice(0, 3).map((project) => (
              <Link
                className="group rounded-2xl border border-[#eef0f3] bg-white p-5 transition hover:border-amber/30 hover:shadow-soft"
                key={project.id}
                to={`/project/${project.id}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 space-y-1">
                    <h3 className="truncate text-[15px] font-semibold text-dark group-hover:text-amber transition-colors">
                      {project.title}
                    </h3>
                    <p className="text-[12px] text-muted">
                      {project.research_type || "Sin tipo"} · {project.approach || "Cuantitativo"}
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 shrink-0 text-muted/30 transition group-hover:text-amber group-hover:translate-x-0.5" />
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
