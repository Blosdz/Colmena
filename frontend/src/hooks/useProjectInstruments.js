import { useQuery } from '@tanstack/react-query';

import { getInstrument, listInstrumentVersions, listProjectInstruments } from '../api/instruments.js';

/**
 * Devuelve los instrumentos del proyecto con su versión de trabajo más
 * reciente. El fallback de metadata permite abrir proyectos creados antes
 * de que existiera la relación project_id en instruments.
 */
export function useProjectInstruments(projectId, projectMetadata = {}) {
  return useQuery({
    queryKey: [
      'projectInstruments',
      String(projectId || ''),
      projectMetadata?.instrument_id || null,
      projectMetadata?.instrument_version_id || null,
    ],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const page = await listProjectInstruments(projectId, { page: 1, pageSize: 100 });
      const instruments = [...(page?.items || [])];
      const legacyId = Number(projectMetadata?.instrument_id || 0);

      if (legacyId && !instruments.some((item) => item.id === legacyId)) {
        try {
          instruments.push(await getInstrument(legacyId));
        } catch {
          // El vínculo legado puede apuntar a un instrumento ya eliminado.
        }
      }

      return Promise.all(
        instruments.map(async (instrument) => {
          const versions = await listInstrumentVersions(instrument.id);
          const legacyVersionId =
            instrument.id === legacyId ? Number(projectMetadata?.instrument_version_id || 0) : 0;
          const version = versions.find((item) => item.id === legacyVersionId) || versions[0] || null;
          return {
            ...instrument,
            versions,
            version,
            versionId: version?.id || null,
            versionCode: version?.version_code || null,
          };
        }),
      );
    },
  });
}
