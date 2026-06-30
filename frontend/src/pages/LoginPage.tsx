import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { env } from "../config/env";
import { isAuthenticated } from "../auth/session";

function HexagonIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2 21 7v10l-9 5-9-5V7l9-5z" />
    </svg>
  );
}

export function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated()) {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  const handleConnect = () => {
    const callback = `${window.location.origin}/auth/callback`;
    const base = env.appThesisSsoUrl;
    const separator = base.includes("?") ? "&" : "?";
    window.location.href = `${base}${separator}redirect=${encodeURIComponent(callback)}`;
  };

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
          <h1 className="mb-2 text-2xl font-semibold tracking-tight text-slate-900">
            Bienvenido de nuevo
          </h1>
          <p className="text-sm text-slate-500">
            Inicia sesión para continuar con tu tesis
          </p>
        </div>

        <div className="flex flex-col items-center gap-4">
          <button
            type="button"
            onClick={handleConnect}
            className="flex h-16 w-full items-center justify-center gap-2 rounded-lg border-2 border-[#E6C200] bg-[#FFD700] text-sm font-semibold uppercase tracking-widest text-[#191b23] shadow-md transition-all hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]"
          >
            <HexagonIcon />
            Conectarte con tu cuenta de AppThesis
          </button>
          <p className="mt-2 text-center text-sm italic text-slate-400">
            La vinculación se realizará de forma automática
          </p>
        </div>
      </div>
    </main>
  );
}

export default LoginPage;
