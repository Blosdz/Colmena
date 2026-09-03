import { useState } from "react";
import { Link } from "react-router-dom";

import { authApi } from "../api/auth";
import { AuthShell, authButtonClass, authInputClass } from "../components/auth/AuthShell";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [resetUrl, setResetUrl] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      const res = await authApi.requestPasswordReset(email.trim());
      setResetUrl(res.reset_url);
      setSent(true);
    } catch {
      // El backend responde igual exista o no la cuenta: nunca mostramos error aquí.
      setSent(true);
    }
    setSubmitting(false);
  };

  return (
    <AuthShell
      title="Recuperar contraseña"
      subtitle="Te enviaremos un enlace para crear una nueva"
    >
      {sent ? (
        <div className="flex flex-col gap-4 text-sm text-slate-600">
          <p>
            Si hay una cuenta con <b>{email.trim()}</b>, recibirás un correo con el enlace
            para restablecer tu contraseña.
          </p>
          {resetUrl && (
            <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs">
              <p className="mb-1 font-semibold text-amber-800">Modo desarrollo — sin correo:</p>
              <a href={resetUrl} className="break-all font-medium text-amber-900 underline">
                {resetUrl}
              </a>
            </div>
          )}
          <Link to="/login" className="text-center font-semibold text-[#191b23] underline">
            Volver a iniciar sesión
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Correo
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={authInputClass}
            />
          </label>
          <button type="submit" disabled={submitting} className={authButtonClass}>
            {submitting ? "Enviando…" : "Enviar enlace"}
          </button>
          <Link to="/login" className="mt-2 text-center text-sm text-slate-500 hover:text-[#191b23] hover:underline">
            Volver a iniciar sesión
          </Link>
        </form>
      )}
    </AuthShell>
  );
}

export default ForgotPasswordPage;
