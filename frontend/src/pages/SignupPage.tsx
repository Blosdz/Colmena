import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { authApi } from "../api/auth";
import { isAuthenticated, setStoredToken, setStoredUser } from "../auth/session";

export function SignupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await authApi.register({ name: name.trim(), email: email.trim(), password });
      setStoredToken(res.token);
      setStoredUser(res.user);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la cuenta.");
      setSubmitting(false);
    }
  };

  const inputClass =
    "mt-1 h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-[#E6C200] focus:ring-2 focus:ring-[#FFD700]/40";

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-white to-blue-50 px-4">
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-cover bg-center opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 30%, rgba(59,130,246,0.18), transparent 45%), radial-gradient(circle at 80% 70%, rgba(255,215,0,0.16), transparent 45%)",
        }}
      />

      <div className="relative z-10 w-full max-w-[480px] rounded-2xl border border-white/70 bg-white/70 p-8 shadow-[0_28px_74px_rgba(15,23,42,0.14)] backdrop-blur-xl sm:p-10">
        <div className="mb-8 text-center">
          <h1 className="mb-2 text-2xl font-semibold tracking-tight text-slate-900">Crea tu cuenta</h1>
          <p className="text-sm text-slate-500">Empieza a recolectar y analizar los datos de tu tesis</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Nombre
            <input
              type="text"
              required
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={inputClass}
            />
          </label>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Correo
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
            />
          </label>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Contraseña
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </label>

          {error && <p className="text-sm font-medium text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="mt-1 h-11 w-full rounded-lg border-2 border-[#E6C200] bg-[#FFD700] text-sm font-semibold uppercase tracking-widest text-[#191b23] shadow-md transition-all hover:shadow-lg active:scale-[0.98] disabled:opacity-60"
          >
            {submitting ? "Creando…" : "Crear cuenta"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-500">
          ¿Ya tienes cuenta?{" "}
          <Link to="/login" className="font-semibold text-[#191b23] underline">
            Inicia sesión
          </Link>
        </p>
      </div>
    </main>
  );
}

export default SignupPage;
