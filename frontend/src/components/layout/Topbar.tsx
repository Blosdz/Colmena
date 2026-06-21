import { useQuery } from "@tanstack/react-query";
import { Bell, RefreshCcw, Search, Wifi, WifiOff } from "lucide-react";

import { apiClient } from "../../api/client";

export function Topbar() {
  const { data, refetch, isFetching } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiClient.get<{ status?: string }>("/api/health"),
    retry: 1,
    refetchInterval: 30000,
  });

  const connected = data?.status?.toLowerCase() === "ok";

  return (
    <div className="sticky top-0 z-10 h-[64px] border-b border-[#eef0f3] bg-white/80 px-8 backdrop-blur-xl">
      <div className="mx-auto flex h-full max-w-[1440px] items-center justify-between gap-6">
        {/* Search */}
        <div className="flex min-w-0 flex-1 items-center">
          <div className="group flex h-10 min-w-0 w-full max-w-[420px] items-center gap-2.5 rounded-xl border border-[#eef0f3] bg-[#f8f9fb] px-4 transition-all hover:border-[#dfe2e6] hover:bg-white focus-within:border-amber focus-within:bg-white focus-within:ring-2 focus-within:ring-amber/10">
            <Search className="h-4 w-4 shrink-0 text-muted/50" />
            <input
              className="min-w-0 flex-1 bg-transparent text-sm text-dark placeholder:text-muted/50 outline-none"
              placeholder="Buscar proyectos, formularios o respuestas..."
              type="text"
            />
          </div>
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-2">
          {/* API Status */}
          <div className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium ${connected ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"}`}>
            {connected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {connected ? "API" : "Sin API"}
          </div>

          {/* Refresh */}
          <button
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[#eef0f3] bg-white text-muted transition hover:bg-[#f5f6f8] hover:text-dark"
            onClick={() => refetch()}
            title="Refrescar conexión"
            type="button"
          >
            <RefreshCcw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
          </button>

          {/* Notifications */}
          <button
            aria-label="Notificaciones"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[#eef0f3] bg-white text-muted transition hover:bg-[#f5f6f8] hover:text-dark"
            type="button"
          >
            <Bell className="h-3.5 w-3.5" />
          </button>

          {/* Divider */}
          <div className="mx-1 h-6 w-px bg-[#eef0f3]" />

          {/* User */}
          <div className="flex items-center gap-2.5 rounded-xl px-2 py-1.5 transition hover:bg-[#f5f6f8] cursor-pointer">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber to-honey text-xs font-bold text-white">
              I
            </div>
            <div className="text-left hidden lg:block">
              <p className="text-[13px] font-semibold text-dark leading-tight">Investigador</p>
              <p className="text-[11px] text-muted leading-tight">admin@colmena.io</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
