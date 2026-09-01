import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { linkAppthesis } from '../api/auth.js';
import { setStoredToken } from '../api/client.js';
import { useAuth } from '../auth/AuthContext.jsx';

/**
 * Aterrizaje del cross-login con AppThesis (monorepo fullProyect).
 * El puente SSO de AppThesis redirige aquí con `?token=<JWT de AppThesis>`.
 * Guardamos el token, vinculamos/espejamos la cuenta en COLMENA y entramos.
 */
export default function AuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { reload } = useAuth();
  const done = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (done.current) return;
    done.current = true;

    const token = params.get('token');
    const next = params.get('redirect') || '/colmena';
    if (!token) {
      setError('No se recibió un token de AppThesis.');
      return;
    }

    (async () => {
      try {
        setStoredToken(token);
        await linkAppthesis(token);
        await reload?.();
        navigate(next, { replace: true });
      } catch {
        setError('No se pudo validar la sesión de AppThesis. Vuelve a intentarlo.');
      }
    })();
  }, [params, navigate, reload]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-hero-glow px-4">
      <div className="colmena-card max-w-md px-8 py-10 text-center">
        {error ? (
          <>
            <p className="text-lg font-bold text-dark">No se pudo iniciar sesión</p>
            <p className="mt-2 text-sm text-muted">{error}</p>
          </>
        ) : (
          <p className="text-sm text-muted">Conectando tu cuenta de AppThesis…</p>
        )}
      </div>
    </div>
  );
}
