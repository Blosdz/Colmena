import { useEffect } from 'react';

import { setActiveProjectId } from '../utils/activeProject.js';

/**
 * Persiste el proyecto activo en localStorage al entrar a cualquier ruta
 * anidada bajo /colmena/project/:projectId, para que el Sidebar lo recuerde
 * incluso al navegar a rutas fuera del árbol de proyecto.
 */
export function useActiveProject(projectId) {
  useEffect(() => {
    if (projectId) setActiveProjectId(String(projectId));
  }, [projectId]);
}
