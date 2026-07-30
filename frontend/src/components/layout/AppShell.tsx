import { useState, type PropsWithChildren } from "react";

import { useLocation } from "react-router-dom";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { ColmenaMenuButton } from "./ColmenaMenuButton";

export function AppShell({ children }: PropsWithChildren) {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  // El wizard de un proyecto EXISTENTE vive en /project/:id (sin "/new" ni ningún otro
  // substring de la lista de abajo), así que necesita su propio match explícito o cae
  // en la rama centrada/sin alto y pierde ancho y alto completos.
  const isProjectWorkspace = /^\/project\/[^/]+$/.test(location.pathname);
  const isWorkspace = isProjectWorkspace || location.pathname.includes("/new") || location.pathname.includes("/workspace") || location.pathname.includes("/builder") || location.pathname.includes("/form");

  return (
    <div className="min-h-screen bg-transparent">
      <div className="flex min-h-screen">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <Topbar />
          <main className={isWorkspace ? "flex-1 flex flex-col" : "flex-1 "}>
            {isWorkspace ? (
              children
            ) : (
              <div className="mx-auto flex flex-col ">
                {children}
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Botón flotante para reabrir el sidebar cuando está contraído */}
      {collapsed && (
        <ColmenaMenuButton
          onClick={() => setCollapsed(false)}
          title="Mostrar menú"
          className="fixed left-3 top-3 z-30 hidden rounded-xl border border-[#E6E8EB] bg-white/95 p-2.5 shadow-sm backdrop-blur transition hover:border-amber/40 hover:shadow-md lg:flex"
        />
      )}
    </div>
  );
}
