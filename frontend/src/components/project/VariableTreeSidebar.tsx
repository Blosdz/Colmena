import { ChevronDown, ChevronRight, Plus, Sigma, Layers, ListChecks, SlidersHorizontal, BarChart3, Database, FolderOpen, X, Check, Users } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { cn } from "../../utils/cn";
import { listProjects } from "../../api/projects";
import { setActiveProjectId } from "../../utils/activeProject";
import type { VariableDraft, VariableTab } from "../../utils/projectDraftStore";

type Props = {
  projectTitle?: string;
  variables: VariableDraft[];
  activeVariableId: string;
  activeTab: VariableTab;
  dataRowCount: number;
  participantFieldCount: number;
  onSelectNode: (varId: string, tab: VariableTab) => void;
  onSelectDataTab: () => void;
  onSelectParticipants: () => void;
  onAddVariable: () => void;
  onRemoveVariable: (id: string) => void;
  onRenameVariable: (id: string, name: string) => void;
  onShowProjectInfo: () => void;
};

// "scale" se fusionó dentro de "items" (editor colapsable), ya no es un nodo propio.
const VAR_TABS: VariableTab[] = ["variable", "dimensions", "items", "baremos"];

const TAB_ICONS: Record<string, React.ElementType> = {
  variable: Sigma,
  dimensions: Layers,
  items: ListChecks,
  scale: SlidersHorizontal,
  baremos: BarChart3,
  data: Database,
};

const TAB_LABELS: Record<string, string> = {
  variable: "Variable",
  dimensions: "Dimensiones",
  items: "Ítems",
  scale: "Escala",
  baremos: "Baremos",
  data: "Base de datos",
};

function completionPercent(v: VariableDraft): number {
  let score = 0;
  if (v.name) score += 1;
  if (v.dimensions.length > 0) score += 1;
  if (v.items.length > 0) score += 1;
  if (v.scale.options.length > 0) score += 1;
  return Math.round((score / 4) * 100);
}

export function VariableTreeSidebar({
  projectTitle,
  variables,
  activeVariableId,
  activeTab,
  dataRowCount,
  participantFieldCount,
  onSelectNode,
  onSelectDataTab,
  onSelectParticipants,
  onAddVariable,
  onRemoveVariable,
  onRenameVariable,
  onShowProjectInfo,
}: Props) {
  const navigate = useNavigate();
  const { projectId: routeProjectId } = useParams();
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [editingId, setEditingId] = useState<string | null>(null);
  const [projectMenuOpen, setProjectMenuOpen] = useState(false);
  const projectMenuRef = useRef<HTMLDivElement>(null);

  const toggle = (id: string) => setCollapsed(prev => ({ ...prev, [id]: !prev[id] }));

  const projectsQuery = useQuery({ queryKey: ["sidebar-project-list"], queryFn: listProjects });
  const projects = projectsQuery.data?.items ?? [];

  // Cerrar el combo al hacer clic fuera
  useEffect(() => {
    if (!projectMenuOpen) return;
    const handler = (e: MouseEvent) => {
      if (projectMenuRef.current && !projectMenuRef.current.contains(e.target as Node)) {
        setProjectMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [projectMenuOpen]);

  const handleSelectProject = (id: string) => {
    setProjectMenuOpen(false);
    if (id === routeProjectId) return;
    setActiveProjectId(id);
    navigate(`/project/${id}`);
  };

  const displayTitle = projectTitle?.trim() || "Proyecto sin título";

  return (
    <div className="w-[215px] shrink-0 flex flex-col border-r border-colmena-border bg-white/80 backdrop-blur-sm">
      {/* Project node — título + combo de proyectos */}
      <div ref={projectMenuRef} className="relative border-b border-colmena-border">
        <div className="flex items-center gap-1 px-2 py-2">
          <button
            onClick={onShowProjectInfo}
            className="flex flex-1 min-w-0 items-center gap-2 px-1 py-1 rounded-md text-left hover:bg-colmena-bg transition-colors"
            title={displayTitle}
          >
            <FolderOpen className="w-4 h-4 text-amber shrink-0" strokeWidth={2} />
            <span className="text-[13px] font-bold text-dark truncate">{displayTitle}</span>
          </button>
          <button
            onClick={() => setProjectMenuOpen((o) => !o)}
            className="shrink-0 p-1 rounded-md text-muted hover:text-dark hover:bg-colmena-bg transition-colors"
            title="Cambiar de proyecto"
            aria-label="Cambiar de proyecto"
          >
            <ChevronDown className={cn("w-4 h-4 transition-transform", projectMenuOpen && "rotate-180")} />
          </button>
        </div>

        {projectMenuOpen && (
          <div className="absolute left-2 right-2 top-full z-20 mt-1 max-h-64 overflow-y-auto rounded-lg border border-colmena-border bg-white shadow-lg">
            {projectsQuery.isLoading ? (
              <div className="px-3 py-2 text-[12px] text-muted">Cargando proyectos…</div>
            ) : projects.length === 0 ? (
              <div className="px-3 py-2 text-[12px] text-muted">Sin proyectos</div>
            ) : (
              projects.map((project) => {
                const isCurrent = project.id === routeProjectId;
                return (
                  <button
                    key={project.id}
                    onClick={() => handleSelectProject(project.id)}
                    className={cn(
                      "flex w-full items-center gap-2 px-3 py-2 text-left text-[12.5px] transition-colors",
                      isCurrent ? "bg-amber/10 text-dark font-semibold" : "text-muted hover:bg-colmena-bg hover:text-dark"
                    )}
                  >
                    <span className="flex-1 truncate">{project.title}</span>
                    {isCurrent && <Check className="w-3.5 h-3.5 text-amber shrink-0" />}
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* Datos del participante (nivel de proyecto) */}
      <button
        onClick={onSelectParticipants}
        className={cn(
          "flex items-center gap-1.5 mx-2 mt-1 px-2 py-1 rounded-md text-left transition-all duration-100",
          activeTab === "participants"
            ? "bg-amber/12 text-dark font-semibold"
            : "text-muted hover:text-dark hover:bg-colmena-bg"
        )}
      >
        <Users className={cn("w-3.5 h-3.5 shrink-0", activeTab === "participants" ? "text-amber" : "")} strokeWidth={activeTab === "participants" ? 2.2 : 1.6} />
        <span className="text-[12.5px] flex-1">Datos del participante</span>
        {participantFieldCount > 0 && (
          <span className={cn(
            "text-[9px] font-bold rounded px-1 py-px leading-none",
            activeTab === "participants" ? "bg-amber/20 text-amber" : "bg-colmena-bg text-muted"
          )}>
            {participantFieldCount}
          </span>
        )}
      </button>

      {/* Variable tree */}
      <div className="flex-1 overflow-y-auto py-1 space-y-0">
        {variables.map((v) => {
          const isOpen = !collapsed[v.id];
          const isActive = v.id === activeVariableId;
          const pct = completionPercent(v);

          return (
            <div key={v.id}>
              {/* Variable header */}
              <div
                className={cn(
                  "group flex items-center gap-1 pl-2 pr-1.5 py-1 cursor-pointer transition-all duration-100",
                  isActive ? "bg-amber/8" : "hover:bg-colmena-bg"
                )}
                onClick={() => { toggle(v.id); if (!isActive) onSelectNode(v.id, activeTab); }}
              >
                <button className="shrink-0 p-0.5" onClick={(e) => { e.stopPropagation(); toggle(v.id); }}>
                  {isOpen
                    ? <ChevronDown className="w-3 h-3 text-muted" />
                    : <ChevronRight className="w-3 h-3 text-muted" />
                  }
                </button>

                {editingId === v.id ? (
                  <input
                    className="flex-1 min-w-0 bg-transparent text-[13px] font-semibold text-dark outline-none border-b border-amber py-0"
                    value={v.name}
                    autoFocus
                    onChange={(e) => onRenameVariable(v.id, e.target.value)}
                    onBlur={() => setEditingId(null)}
                    onKeyDown={(e) => { if (e.key === "Enter") setEditingId(null); }}
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <span
                    className={cn(
                      "flex-1 text-[13px] font-semibold truncate min-w-0",
                      isActive ? "text-dark" : "text-muted"
                    )}
                    onDoubleClick={(e) => { e.stopPropagation(); setEditingId(v.id); }}
                  >
                    {v.name}
                  </span>
                )}

                {/* Completion pill */}
                <span className={cn(
                  "shrink-0 text-[9px] font-bold rounded-full px-1 py-px leading-none",
                  pct === 100 ? "bg-success/15 text-success" : "bg-colmena-border text-muted"
                )}>
                  {pct}%
                </span>

                {/* Remove (only if >1) */}
                {variables.length > 1 && (
                  <button
                    className="shrink-0 p-0.5 opacity-0 group-hover:opacity-100 transition-opacity text-muted hover:text-danger"
                    onClick={(e) => { e.stopPropagation(); onRemoveVariable(v.id); }}
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                )}
              </div>

              {/* Child nodes (tabs) */}
              {isOpen && (
                <div className="pl-5 space-y-0">
                  {VAR_TABS.map((tab) => {
                    const Icon = TAB_ICONS[tab];
                    const isTabActive = isActive && activeTab === tab;

                    let badge = "";
                    if (tab === "dimensions") badge = String(v.dimensions.length);
                    if (tab === "items") badge = String(v.items.length);
                    if (tab === "scale") badge = String(v.scale.options.length);
                    if (tab === "baremos") badge = String(v.baremos.length);

                    return (
                      <button
                        key={tab}
                        onClick={() => onSelectNode(v.id, tab)}
                        className={cn(
                          "flex items-center gap-1.5 w-full pl-2 pr-1.5 py-1 text-left transition-all duration-100 rounded-r-md",
                          isTabActive
                            ? "bg-amber/12 text-dark font-semibold"
                            : "text-muted hover:text-dark hover:bg-colmena-bg"
                        )}
                      >
                        <Icon className={cn("w-3.5 h-3.5 shrink-0", isTabActive ? "text-amber" : "")} strokeWidth={isTabActive ? 2.2 : 1.6} />
                        <span className="text-[12.5px] flex-1">{TAB_LABELS[tab]}</span>
                        {badge !== "" && badge !== "0" && (
                          <span className={cn(
                            "text-[9px] font-bold rounded px-1 py-px leading-none",
                            isTabActive ? "bg-amber/20 text-amber" : "bg-colmena-bg text-muted"
                          )}>
                            {badge}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Data tab (global) */}
      <button
        onClick={onSelectDataTab}
        className={cn(
          "flex items-center gap-1.5 mx-2 my-0.5 px-2 py-1 rounded-md text-left transition-all duration-100",
          activeTab === "data"
            ? "bg-amber/12 text-dark font-semibold"
            : "text-muted hover:text-dark hover:bg-colmena-bg"
        )}
      >
        <Database className={cn("w-3.5 h-3.5 shrink-0", activeTab === "data" ? "text-amber" : "")} strokeWidth={activeTab === "data" ? 2.2 : 1.6} />
        <span className="text-[12.5px] flex-1">Base de datos</span>
        {dataRowCount > 0 && (
          <span className={cn(
            "text-[9px] font-bold rounded px-1 py-px leading-none",
            activeTab === "data" ? "bg-amber/20 text-amber" : "bg-colmena-bg text-muted"
          )}>
            {dataRowCount}
          </span>
        )}
      </button>

      {/* Add variable */}
      <div className="border-t border-colmena-border p-2">
        <button
          onClick={onAddVariable}
          className="flex items-center gap-1.5 w-full justify-center rounded-md border border-dashed border-colmena-border py-1.5 text-[12px] font-semibold text-muted hover:text-amber hover:border-amber/40 hover:bg-amber/5 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          Agregar variable
        </button>
      </div>
    </div>
  );
}
