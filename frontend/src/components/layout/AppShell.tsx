import type { PropsWithChildren } from "react";

import { useLocation } from "react-router-dom";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell({ children }: PropsWithChildren) {
  const location = useLocation();
  const isWorkspace = location.pathname.includes("/new") || location.pathname.includes("/workspace") || location.pathname.includes("/builder") || location.pathname.includes("/form");

  return (
    <div className="min-h-screen bg-transparent">
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <Topbar />
          <main className={isWorkspace ? "flex-1 flex flex-col min-h-0" : "flex-1 px-8 py-6"}>
            {isWorkspace ? (
              children
            ) : (
              <div className="mx-auto flex max-w-[1440px] flex-col gap-6">
                {children}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
