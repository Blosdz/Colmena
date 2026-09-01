import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, FolderKanban, Layers, Search, Sparkles } from 'lucide-react';

import { useAuth } from '../../auth/AuthContext.jsx';
import { listProjects } from '../../api/projects.js';
import { PageHeader } from '../../components/layout/PageHeader.jsx';
import { Card } from '../../components/ui/Card.jsx';
import { PrimaryAction } from '../../components/ui/PrimaryAction.jsx';
import MetricCard from '../../components/ui/MetricCard.jsx';
import { StatusPill } from '../../components/ui/StatusPill.jsx';
import { EmptyState } from '../../components/ui/EmptyState.jsx';
import { LoadingState } from '../../components/ui/LoadingState.jsx';
import { ErrorState } from '../../components/ui/ErrorState.jsx';
import ProjectCreateModal from '../../components/colmena/projects/ProjectCreateModal.jsx';
import { displayLabel } from '../../utils/labels.js';

const STATUS_TONE = { ACTIVE: 'active', DRAFT: 'draft', ARCHIVED: 'neutral' };

export default function ArchiveProjectsPage() {
  const { user } = useAuth();
  const [showNewProject, setShowNewProject] = useState(false);
  const [search, setSearch] = useState('');

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['archive-projects'],
    queryFn: () => listProjects({ page: 1, pageSize: 100 }),
  });

  if (isLoading) return <LoadingState label="Cargando proyectos..." />;
  if (isError) return <ErrorState message={error?.message || 'No pudimos cargar los proyectos.'} />;

  const projects = data?.items ?? [];
  const filtered = search.trim()
    ? projects.filter((p) => p.name.toLowerCase().includes(search.trim().toLowerCase()))
    : projects;

  const byType = new Set(projects.map((p) => p.project_type)).size;

  return (
    <div className="colmena-page">
      <PageHeader
        title="Archivo de proyectos"
        description="Retoma cualquier proyecto ya creado. El flujo principal sigue empezando en Crear proyecto."
        actions={<PrimaryAction onClick={() => setShowNewProject(true)}>Crear proyecto</PrimaryAction>}
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <MetricCard icon={FolderKanban} label="Total de proyectos" value={projects.length} />
        <MetricCard icon={Layers} label="Tipos distintos" value={byType} />
        <MetricCard icon={Sparkles} label="Resultado de búsqueda" value={filtered.length} />
      </div>

      {showNewProject && user ? (
        <ProjectCreateModal
          ownerUserId={user.id}
          onClose={() => setShowNewProject(false)}
          onCreated={() => setShowNewProject(false)}
        />
      ) : null}

      <div className="flex h-10 w-full max-w-[520px] items-center gap-2.5 rounded-xl border border-border bg-white px-3 shadow-sm">
        <Search className="h-4 w-4 text-muted" />
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Buscar proyecto por nombre..."
          className="w-full bg-transparent text-sm text-dark outline-none placeholder:text-muted"
        />
      </div>

      {filtered.length === 0 ? (
        <Card>
          <EmptyState
            title={projects.length === 0 ? 'Aún no hay proyectos' : 'Sin resultados'}
            description={
              projects.length === 0
                ? 'Empieza creando el proyecto y luego define variables, dimensiones y preguntas.'
                : 'Ningún proyecto coincide con tu búsqueda.'
            }
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {filtered.map((project) => (
            <Link key={project.id} to={`/colmena/project/${project.id}`}>
              <Card className="flex h-full flex-col justify-between gap-3 transition hover:-translate-y-0.5 hover:shadow-glow">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber/10 text-amber">
                    <FolderKanban size={20} />
                  </div>
                  <StatusPill label={displayLabel(project.status)} tone={STATUS_TONE[project.status] || 'neutral'} />
                </div>
                <div>
                  <p className="text-base font-semibold text-dark">{project.name}</p>
                  <p className="mt-1 text-xs text-muted">{displayLabel(project.project_type)}</p>
                </div>
                <span className="inline-flex items-center gap-1 text-sm font-medium text-amber">
                  Abrir proyecto <ArrowRight size={14} />
                </span>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
