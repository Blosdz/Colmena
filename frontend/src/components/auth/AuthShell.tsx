import type { PropsWithChildren } from "react";

/** Marco visual compartido por las páginas de autenticación de Colmena. */
export function AuthShell({
  title,
  subtitle,
  children,
}: PropsWithChildren<{ title: string; subtitle: string }>) {
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
          <h1 className="mb-2 text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>
        {children}
      </div>
    </main>
  );
}

export const authInputClass =
  "mt-1 h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-[#E6C200] focus:ring-2 focus:ring-[#FFD700]/40";

export const authButtonClass =
  "mt-1 h-11 w-full rounded-lg border-2 border-[#E6C200] bg-[#FFD700] text-sm font-semibold uppercase tracking-widest text-[#191b23] shadow-md transition-all hover:shadow-lg active:scale-[0.98] disabled:opacity-60";
