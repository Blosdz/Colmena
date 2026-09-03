import { useNavigate } from "react-router-dom";

import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";
import { clearStoredUser, getStoredUser } from "../auth/session";
import { clearActiveProjectId } from "../utils/activeProject";

export function SettingsPage() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const isSso = Boolean(user?.appthesis_user_id);

  const handleLogout = () => {
    clearStoredUser();
    clearActiveProjectId();
    navigate("/login", { replace: true });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Configuración"
        description="Aquí quedarán los ajustes generales del espacio de trabajo, la marca y los formatos de salida."
      />

      {user && (
        <section className="rounded-xl border border-[#eef0f3] bg-white p-5">
          <h2 className="text-sm font-semibold text-dark">Cuenta</h2>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted">Nombre</dt>
              <dd className="text-dark">{user.name}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted">Correo</dt>
              <dd className="text-dark">{user.email}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted">Tipo de acceso</dt>
              <dd className="text-dark">
                {isSso ? "Vinculada con AppThesis" : "Cuenta de Colmena (correo y contraseña)"}
              </dd>
            </div>
          </dl>
          <div className="mt-4 flex flex-wrap gap-2">
            {!isSso && (
              <a
                href="/forgot-password"
                className="inline-flex h-9 items-center rounded-lg border border-[#eef0f3] bg-white px-3 text-sm font-medium text-dark hover:bg-[#f5f6f8]"
              >
                Cambiar contraseña
              </a>
            )}
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex h-9 items-center rounded-lg border border-[#eef0f3] bg-white px-3 text-sm font-medium text-red-500 hover:bg-red-50"
            >
              Cerrar sesión
            </button>
          </div>
        </section>
      )}

      <EmptyState
        title="Configuración en preparación"
        description="La fase actual está centrada en el flujo del estudio. Los ajustes globales se integrarán después."
      />
    </div>
  );
}
