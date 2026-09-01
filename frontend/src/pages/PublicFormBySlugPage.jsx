import { useQuery } from '@tanstack/react-query';
import { Navigate, useParams } from 'react-router-dom';

import { getPublicFormBySlug } from '../api/public.js';
import { BrandMark } from '../brand/BrandMark.jsx';

/**
 * Compatibilidad con AppThesis: éste embebe `/public/forms/:slug` en un iframe.
 * El `slug` puede ser el `public_id` del estudio o el slug heredado del COLMENA
 * anterior. Se resuelve contra el shim y se continúa por la ruta normal
 * `/encuesta/:publicId`.
 */
export default function PublicFormBySlugPage() {
  const { slug } = useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['publicFormSlug', slug],
    queryFn: () => getPublicFormBySlug(slug),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-hero-glow">
        <div className="colmena-card px-8 py-6 text-sm text-muted">Cargando…</div>
      </div>
    );
  }

  if (isError || !data?.study_public_id) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-hero-glow px-4">
        <div className="colmena-card max-w-md px-8 py-10 text-center">
          <BrandMark className="mx-auto mb-4 h-8 w-8" />
          <p className="text-lg font-bold text-dark">Esta encuesta no está disponible.</p>
          <p className="mt-2 text-sm text-muted">
            El enlace puede estar mal escrito, o el estudio todavía no está abierto para respuestas.
          </p>
        </div>
      </div>
    );
  }

  return <Navigate to={`/encuesta/${data.study_public_id}`} replace />;
}
