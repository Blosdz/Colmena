import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { authApi } from "../api/auth";
import { setStoredToken, setStoredUser } from "../auth/session";

export function AuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const token = params.get("token");
    if (!token) {
      setError("No se recibió ningún token de AppThesis.");
      return;
    }

    authApi
      .linkAppThesis(token)
      .then((res) => {
        setStoredToken(token);
        setStoredUser(res.user);
        navigate("/", { replace: true });
      })
      .catch((err: unknown) => {
        const message =
          err instanceof Error ? err.message : "No se pudo vincular la cuenta.";
        setError(message);
      });
  }, [params, navigate]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 px-4 text-center text-slate-700">
      {error ? (
        <>
          <p className="text-sm font-medium text-red-600">{error}</p>
          <button
            type="button"
            onClick={() => navigate("/login", { replace: true })}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Volver a intentar
          </button>
        </>
      ) : (
        <>
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#FFD700] border-t-transparent" />
          <p className="text-sm font-medium">Vinculando tu cuenta de AppThesis…</p>
        </>
      )}
    </main>
  );
}

export default AuthCallbackPage;
