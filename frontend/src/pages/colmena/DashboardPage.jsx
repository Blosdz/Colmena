import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Archive, FolderKanban, Plus, Send } from 'lucide-react';

import { useAuth } from '../../auth/AuthContext.jsx';
import { listProjects } from '../../api/projects.js';
import { Card } from '../../components/ui/Card.jsx';
import MetricCard from '../../components/ui/MetricCard.jsx';
import { PrimaryAction } from '../../components/ui/PrimaryAction.jsx';
import { LoadingState } from '../../components/ui/LoadingState.jsx';
import { ErrorState } from '../../components/ui/ErrorState.jsx';
import ProjectCreateModal from '../../components/colmena/projects/ProjectCreateModal.jsx';
import { displayLabel } from '../../utils/labels.js';

const FLOW_STEPS = ['Proyecto', 'Variables y dimensiones', 'Datos exógenos', 'Formulario', 'Link', 'Respuestas'];

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showCreateProject, setShowCreateProject] = useState(false);
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['projects', { page: 1 }],
    queryFn: () => listProjects({ page: 1, pageSize: 10 }),
  });

  if (isLoading) return <LoadingState label="Cargando tu espacio de trabajo..." />;
  if (isError) return <ErrorState message={error?.message || 'No pudimos cargar tus proyectos.'} />;

  const projects = data?.items ?? [];
  const latestProject = projects[0];
  const displayName = user?.first_name || user?.username || '';

  return (
    <div className="colmena-page">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(260px,0.7fr)]">
        <div className="relative overflow-hidden rounded-2xl border border-border bg-surface bg-hero-glow p-5 sm:p-4 shadow-card">
          <p className="colmena-label">Hola, {displayName}</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-dark">Bienvenido a tu espacio en Colmena</h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-5 text-muted">
            Diseña variables y dimensiones, construye el formulario, recolecta respuestas y analiza resultados — todo
            en un solo flujo.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <PrimaryAction onClick={() => setShowCreateProject(true)}>
              <Plus size={16} className="mr-1" />
              Crear proyecto
            </PrimaryAction>
            {latestProject ? (
              <Link to={`/colmena/project/${latestProject.id}`}>
                <button type="button" className="colmena-button-secondary">
                  Continuar: {latestProject.name}
                </button>
              </Link>
            ) : (
              <Link to="/colmena/archive/projects">
                <button type="button" className="colmena-button-secondary">
                  Ver archivo
                </button>
              </Link>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 xl:grid-cols-1">
          <MetricCard icon={FolderKanban} label="Proyectos" value={projects.length} />
          <Link to="/colmena/archive/projects">
            <Card className="flex h-full items-center gap-3 px-4 py-3 transition hover:-translate-y-0.5 hover:shadow-glow">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-turquoise/10 text-turquoise">
                <Archive size={20} />
              </div>
              <div>
                <p className="colmena-label">Archivo</p>
                <p className="text-sm font-semibold text-dark">Ver todos los proyectos</p>
              </div>
            </Card>
          </Link>
        </div>
      </div>

      <Card>
        <p className="mb-3 colmena-label">Flujo metodológico</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {FLOW_STEPS.map((step, index) => (
            <div key={step} className="rounded-xl border border-border bg-surfaceSoft px-3 py-3 text-center">
              <p className="text-[11px] font-semibold text-amber">{index + 1}</p>
              <p className="mt-1 text-[13px] font-medium text-dark">{step}</p>
            </div>
          ))}
        </div>
      </Card>

      {showCreateProject && user ? (
        <ProjectCreateModal
          ownerUserId={user.id}
          onClose={() => setShowCreateProject(false)}
          onCreated={(project) => navigate(`/colmena/project/${project.id}`)}
        />
      ) : null}

      {projects.length > 0 ? (
        <div>
          <div className="mb-3 flex items-center justify-between">
            <p className="colmena-label">Proyectos recientes</p>
            <Link to="/colmena/archive/projects" className="inline-flex items-center gap-1 text-sm font-medium text-amber hover:underline">
              Ver todos
              <Send size={13} />
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {projects.slice(0, 6).map((project) => (
              <Link key={project.id} to={`/colmena/project/${project.id}`}>
                <Card className="flex h-full flex-col justify-between gap-3 transition hover:-translate-y-0.5 hover:shadow-glow">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber/10 text-amber">
                    <FolderKanban size={18} />
                  </div>
                  <div>
                    <p className="font-semibold text-dark">{project.name}</p>
                    <p className="mt-1 text-xs text-muted">{displayLabel(project.project_type)}</p>
                  </div>
                  <span className="inline-flex items-center gap-1 text-sm font-medium text-amber">
                    Abrir <ArrowRight size={14} />
                  </span>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
