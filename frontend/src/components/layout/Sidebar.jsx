import {
  Archive,
  BarChart3,
  BookOpen,
  CalendarCheck,
  ChevronDown,
  ClipboardList,
  FileBarChart2,
  FolderKanban,
  FileDown,
  FlaskConical,
  Gauge,
  Home,
  LayoutDashboard,
  ListChecks,
  Plus,
  Settings,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { listProjects } from '../../api/projects.js';
import { BrandLogo } from '../../brand/BrandLogo.jsx';

import { cn } from '../../utils/cn.js';
import { displayLabel } from '../../utils/labels.js';
import { getActiveProjectId, setActiveProjectId } from '../../utils/activeProject.js';
import { ColmenaMenuButton } from './ColmenaMenuButton.jsx';

/**
 * Portado de fullProyect/COLMENA/frontend (Sidebar.tsx). Misma resolución de
 * "proyecto activo" (URL > localStorage), mismos 3 grupos de navegación,
 * adaptado a nuestras rutas reales bajo /colmena y a nuestro `listProjects`
 * (Page<ProjectRead>: items[].id/name/status en vez de title).
 */
export function Sidebar({ collapsed = false, onToggle }) {
  const location = useLocation();
  const navigate = useNavigate();

  const match = location.pathname.match(/^\/colmena\/project\/([a-zA-Z0-9-]+)/);
  const routeProjectId = match ? match[1] : null;
  const activeProjectId = routeProjectId && routeProjectId !== 'new' ? routeProjectId : getActiveProjectId();

  const hasProject = Boolean(activeProjectId && activeProjectId !== 'new');

  const projectsQuery = useQuery({
    queryKey: ['sidebar-projects'],
    queryFn: () => listProjects({ page: 1, pageSize: 100 }),
  });
  const projects = projectsQuery.data?.items ?? [];

  const handleSelectProject = (event) => {
    const projectId = event.target.value;
    if (!projectId) return;
    setActiveProjectId(projectId);
    navigate(`/colmena/project/${projectId}`);
  };

  const projectSelector = (
    <div className="mb-2 px-1">
      <div className="relative">
        <FolderKanban className="pointer-events-none absolute left-2.5 top-1/2 h-[15px] w-[15px] -translate-y-1/2 text-muted/60" />
        <select
          value={hasProject ? activeProjectId : ''}
          onChange={handleSelectProject}
          disabled={projectsQuery.isLoading || projects.length === 0}
          className="w-full appearance-none rounded-xl border border-[#E6E8EB] bg-white py-2 pl-8 pr-8 text-[12.5px] font-medium text-dark shadow-sm outline-none transition-colors hover:border-amber/40 focus:border-amber/60 focus:ring-1 focus:ring-amber/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <option value="" disabled>
            {projectsQuery.isLoading
              ? 'Cargando proyectos...'
              : projects.length === 0
                ? 'Sin proyectos'
                : 'Selecciona un proyecto'}
          </option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
              {project.status && project.status !== 'ACTIVE' ? ` (${displayLabel(project.status)})` : ''}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted/60" />
      </div>
    </div>
  );

  const projectHref = hasProject ? `/colmena/project/${activeProjectId}` : '/colmena/project/new';
  const instrumentsHref = hasProject ? `/colmena/project/${activeProjectId}/instruments` : '/colmena/project/new';
  const formHref = hasProject ? `/colmena/project/${activeProjectId}/form` : '/colmena/project/new';
  const telemetryHref = hasProject ? `/colmena/project/${activeProjectId}/telemetry` : '/colmena/project/new';
  const resultsHref = hasProject ? `/colmena/project/${activeProjectId}/results` : '/colmena/project/new';
  const premiumHref = hasProject ? `/colmena/project/${activeProjectId}/premium` : '/colmena/project/new';
  const analyticsLabHref = hasProject ? `/colmena/project/${activeProjectId}/analytics-lab` : '/colmena/project/new';
  const planHref = hasProject ? `/colmena/project/${activeProjectId}/plan` : '/colmena/project/new';
  const reportsHref = hasProject ? `/colmena/project/${activeProjectId}/reports` : '/colmena/project/new';
  const exportsHref = hasProject ? `/colmena/project/${activeProjectId}/exports` : '/colmena/project/new';

  const navGroups = [
    {
      items: [
        { to: '/colmena', label: 'Inicio', icon: Home, active: (p) => p === '/colmena' },
        {
          to: '/colmena/project/new',
          label: 'Nuevo proyecto',
          icon: Plus,
          active: (p) => p === '/colmena/project/new',
        },
      ],
    },
    {
      title: 'Proyecto Activo',
      beforeItems: projectSelector,
      items: [
        {
          to: instrumentsHref,
          label: 'Instrumentos',
          icon: BookOpen,
          active: (p) => p.includes('/instruments'),
        },
        {
          to: projectHref,
          label: 'Constructor',
          icon: LayoutDashboard,
          active: (p) => {
            if (!hasProject) return false;
            return p === `/colmena/project/${activeProjectId}` || p === `/colmena/project/${activeProjectId}/builder`;
          },
        },
        { to: formHref, label: 'Formulario', icon: ListChecks, active: (p) => p.includes('/form') },
        {
          to: telemetryHref,
          label: 'Telemetría',
          icon: BarChart3,
          active: (p) => p.includes('/telemetry') || p.includes('/link'),
        },
        { to: resultsHref, label: 'Resultados', icon: ClipboardList, active: (p) => p.includes('/results') },
        { to: premiumHref, label: 'Explorador', icon: Gauge, active: (p) => p.includes('/premium') },
        {
          to: analyticsLabHref,
          label: 'Panel visual',
          icon: FlaskConical,
          active: (p) => p.includes('/analytics-lab'),
        },
        { to: planHref, label: 'Plan preventivo', icon: CalendarCheck, active: (p) => p.includes('/plan') },
        { to: reportsHref, label: 'Reportes', icon: FileBarChart2, active: (p) => p.includes('/reports') },
        { to: exportsHref, label: 'Exportaciones', icon: FileDown, active: (p) => p.includes('/exports') },
      ],
    },
    {
      title: 'Sistema',
      items: [
        {
          to: '/colmena/archive/projects',
          label: 'Archivo',
          icon: Archive,
          active: (p) => p.includes('/archive'),
        },
        { to: '/colmena/settings', label: 'Configuración', icon: Settings, active: (p) => p === '/colmena/settings' },
      ],
    },
  ];

  return (
    <aside
      className={cn(
        'hidden shrink-0 overflow-hidden transition-[width] duration-200 ease-in-out lg:block',
        collapsed ? 'lg:w-0' : 'lg:w-[240px]',
      )}
    >
      <div
        className={cn(
          'sticky top-0 flex h-screen w-[240px] flex-col bg-white border-r border-[#E6E8EB] transition-opacity duration-150',
          collapsed && 'pointer-events-none opacity-0',
        )}
      >
        <div className="px-5 pt-5 pb-4">
          <div className="flex items-start justify-between gap-2">
            <BrandLogo />
            <ColmenaMenuButton
              onClick={() => onToggle?.()}
              title="Contraer menú"
              className="mt-0.5 rounded-lg p-1.5 hover:bg-[#F5F6F8]"
            />
          </div>
          <p className="mt-1 pl-[50px] text-[11px] font-medium text-muted/70 tracking-wide">
            Encuestas inteligentes
          </p>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 pt-4 space-y-6">
          {navGroups.map((group, gi) => (
            <div key={gi}>
              {group.title && (
                <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.12em] text-muted/50">
                  {group.title}
                </p>
              )}
              {group.beforeItems}
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = item.active(location.pathname);
                  return (
                    <Link
                      className={cn(
                        'group flex h-10 items-center gap-3 rounded-xl px-3 text-[13.5px] font-medium transition-all duration-150',
                        isActive
                          ? 'bg-gradient-to-r from-amber/10 to-amber/5 text-dark shadow-sm ring-1 ring-amber/15'
                          : 'text-muted hover:bg-[#F5F6F8] hover:text-dark',
                      )}
                      key={item.label}
                      to={item.to}
                    >
                      <item.icon
                        className={cn(
                          'h-[18px] w-[18px] shrink-0 transition-colors',
                          isActive ? 'text-amber' : 'text-muted/60 group-hover:text-muted',
                        )}
                        strokeWidth={isActive ? 2.2 : 1.8}
                      />
                      <span>{item.label}</span>
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

export default Sidebar;
