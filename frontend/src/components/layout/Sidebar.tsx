import {
  Archive,
  BarChart3,
  FileText,
  Home,
  ListChecks,
  Plus,
  Settings,
  Sparkles,
  LayoutDashboard
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { BrandLogo } from "../../brand/BrandLogo";
import { cn } from "../../utils/cn";
import { getActiveProjectId } from "../../utils/activeProject";

type NavItem = {
  to: string;
  label: string;
  icon: React.ElementType;
  active: (path: string) => boolean;
  badge?: string;
};

type NavGroup = {
  title?: string;
  items: NavItem[];
};

export function Sidebar() {
  const location = useLocation();

  // Active project resolution
  // We try to grab it from URL, or fallback to localStorage
  const match = location.pathname.match(/^\/project\/([a-zA-Z0-9-]+)/);
  const routeProjectId = match ? match[1] : null;
  const activeProjectId = (routeProjectId && routeProjectId !== "new") ? routeProjectId : getActiveProjectId();
  
  const hasProject = Boolean(activeProjectId && activeProjectId !== "new");

  const projectHref = hasProject ? `/project/${activeProjectId}` : "/project/new";
  const formHref = hasProject ? `/project/${activeProjectId}/form` : "/project/new";
  const telemetryHref = hasProject ? `/project/${activeProjectId}/telemetry` : "/project/new";
  const resultsHref = hasProject ? `/project/${activeProjectId}/results` : "/project/new";
  const reportsHref = hasProject ? `/project/${activeProjectId}/reports` : "/project/new";

  const navGroups: NavGroup[] = [
    {
      items: [
        {
          to: "/",
          label: "Inicio",
          icon: Home,
          active: (p) => p === "/",
        },
        {
          to: "/project/new",
          label: "Nuevo proyecto",
          icon: Plus,
          active: (p) => p === "/project/new",
        },
      ],
    },
    {
      title: "Proyecto Activo",
      items: [
        {
          to: projectHref,
          label: "Constructor",
          icon: LayoutDashboard,
          active: (p) => {
            if (!hasProject) return false;
            return p === `/project/${activeProjectId}` || p === `/project/${activeProjectId}/builder`;
          },
        },
        {
          to: formHref,
          label: "Formulario",
          icon: ListChecks,
          active: (p) => p.includes("/form"),
        },
        {
          to: telemetryHref,
          label: "Telemetría",
          icon: BarChart3,
          active: (p) => p.includes("/telemetry") || p.includes("/link"),
        },
        {
          to: resultsHref,
          label: "Resultados",
          icon: Sparkles,
          active: (p) => p.includes("/results"),
        },
        {
          to: reportsHref,
          label: "Reportes",
          icon: FileText,
          active: (p) => p.includes("/reports"),
        },
      ],
    },
    {
      title: "Sistema",
      items: [
        {
          to: "/archive/projects",
          label: "Archivo",
          icon: Archive,
          active: (p) => p.includes("/archive"),
        },
        {
          to: "/settings",
          label: "Configuración",
          icon: Settings,
          active: (p) => p === "/settings",
        },
      ],
    }
  ];

  return (
    <aside className="hidden w-[240px] shrink-0 lg:block">
      <div className="sticky top-0 flex h-screen flex-col bg-white border-r border-[#E6E8EB]">
        {/* Header */}
        <div className="px-5 pt-5 pb-4">
          <BrandLogo />
          <p className="mt-1 pl-[50px] text-[11px] font-medium text-muted/70 tracking-wide">
            Resultados inteligentes
          </p>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 pt-4 space-y-6">
          {navGroups.map((group, gi) => (
            <div key={gi}>
              {group.title && (
                <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.12em] text-muted/50">
                  {group.title}
                </p>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = item.active(location.pathname);
                  return (
                    <Link
                      className={cn(
                        "group flex h-10 items-center gap-3 rounded-xl px-3 text-[13.5px] font-medium transition-all duration-150",
                        isActive
                          ? "bg-gradient-to-r from-amber/10 to-amber/5 text-dark shadow-sm ring-1 ring-amber/15"
                          : "text-muted hover:bg-[#F5F6F8] hover:text-dark"
                      )}
                      key={item.label}
                      to={item.to}
                    >
                      <item.icon
                        className={cn(
                          "h-[18px] w-[18px] shrink-0 transition-colors",
                          isActive
                            ? "text-amber"
                            : "text-muted/60 group-hover:text-muted"
                        )}
                        strokeWidth={isActive ? 2.2 : 1.8}
                      />
                      <span>{item.label}</span>
                      {item.badge && (
                        <span className="ml-auto rounded-md bg-amber/10 px-1.5 py-0.5 text-[10px] font-semibold text-amber">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>
    </aside>
  );
}
