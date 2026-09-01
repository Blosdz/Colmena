import { Link } from 'react-router-dom';

import { EmptyState } from '../ui/EmptyState.jsx';

export function ProjectMissingState({ description = 'No pudimos resolver este proyecto.' }) {
  return (
    <EmptyState title="No encontramos este proyecto" description={description}>
      <div className="flex flex-wrap justify-center gap-3">
        <Link to="/colmena/project/new" className="colmena-button-primary">
          Crear proyecto
        </Link>
        <Link to="/colmena/archive/projects" className="colmena-button-secondary">
          Ir al archivo
        </Link>
      </div>
    </EmptyState>
  );
}

export default ProjectMissingState;
