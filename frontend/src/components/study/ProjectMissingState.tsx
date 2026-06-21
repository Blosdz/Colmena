import { Link } from "react-router-dom";

import { EmptyState } from "../ui/EmptyState";

export function ProjectMissingState({
  description = "No pudimos resolver el proyecto solicitado. Puedes crear uno nuevo o abrir uno existente desde el archivo.",
}: {
  description?: string;
}) {
  return (
    <div className="space-y-4">
      <EmptyState
        title="No encontramos este proyecto"
        description={description}
      />
      <div className="flex flex-wrap gap-3">
        <Link className="colmena-button-primary inline-flex items-center justify-center" to="/project/new">
          Crear proyecto
        </Link>
        <Link className="colmena-button-secondary inline-flex items-center justify-center" to="/archive/projects">
          Ir al archivo
        </Link>
      </div>
    </div>
  );
}
