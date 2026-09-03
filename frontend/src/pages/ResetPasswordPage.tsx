import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { authApi } from "../api/auth";
import { AuthShell, authButtonClass, authInputClass } from "../components/auth/AuthShell";
import { setStoredToken, setStoredUser } from "../auth/session";

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await authApi.resetPassword({ token, password });
      setStoredToken(res.token);
      setStoredUser(res.user);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo restablecer la contraseña.");
      setSubmitting(false);
    }
  };

  if (!token) {
    return (
      <AuthShell title="Enlace no válido" subtitle="Falta el token de recuperación">
        <Link to="/forgot-password" className="block text-center font-semibold text-[#191b23] underline">
          Pedir un enlace nuevo
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Nueva contraseña" subtitle="Elige una contraseña para tu cuenta">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Nueva contraseña
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={authInputClass}
          />
        </label>
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Repetir contraseña
          <input
            type="password"
            required
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className={authInputClass}
          />
        </label>

        {error && <p className="text-sm font-medium text-red-600">{error}</p>}

        <button type="submit" disabled={submitting} className={authButtonClass}>
          {submitting ? "Guardando…" : "Cambiar contraseña"}
        </button>
      </form>
    </AuthShell>
  );
}

export default ResetPasswordPage;
