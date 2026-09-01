import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { fetchCurrentUser, loginUser, registerUser } from '../api/auth.js';
import { clearStoredToken, getStoredToken, setStoredToken } from '../api/client.js';

const AuthContext = createContext(null);

// 'appthesis' → el login lo hace AppThesis (monorepo fullProyect) vía un puente
// SSO; 'standalone' → login/registro propios de COLMENA (desarrollo suelto).
export const AUTH_MODE = import.meta.env.VITE_AUTH_MODE === 'appthesis' ? 'appthesis' : 'standalone';

const APPTHESIS_SSO_URL = import.meta.env.VITE_APPTHESIS_SSO_URL || 'http://localhost:5173/#/sso/colmena';

/** Lanza el flujo SSO de AppThesis. Al volver aterriza en /auth/callback?token=. */
export function beginAppthesisSso() {
  const callback = `${window.location.origin}/auth/callback`;
  const separator = APPTHESIS_SSO_URL.includes('?') ? '&' : '?';
  window.location.href = `${APPTHESIS_SSO_URL}${separator}redirect=${encodeURIComponent(callback)}`;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | authenticated | anonymous

  const loadCurrentUser = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setStatus('anonymous');
      return;
    }
    try {
      const currentUser = await fetchCurrentUser();
      setUser(currentUser);
      setStatus('authenticated');
    } catch {
      clearStoredToken();
      setUser(null);
      setStatus('anonymous');
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  const login = useCallback(
    async ({ email, password }) => {
      const { access_token: token } = await loginUser({ email, password });
      setStoredToken(token);
      await loadCurrentUser();
    },
    [loadCurrentUser],
  );

  const signup = useCallback(async (payload) => {
    await registerUser(payload);
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    setUser(null);
    setStatus('anonymous');
  }, []);

  const value = useMemo(
    () => ({ user, status, login, signup, logout, reload: loadCurrentUser }),
    [user, status, login, signup, logout, loadCurrentUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un <AuthProvider>');
  }
  return context;
}

export function ProtectedRoute({ children }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="colmena-card px-8 py-6 text-sm text-muted">Cargando…</div>
      </div>
    );
  }

  if (status === 'anonymous') {
    if (AUTH_MODE === 'appthesis') {
      beginAppthesisSso();
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="colmena-card px-8 py-6 text-sm text-muted">Redirigiendo a AppThesis…</div>
        </div>
      );
    }
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
