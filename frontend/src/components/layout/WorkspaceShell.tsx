import type { PropsWithChildren, ReactNode } from "react";

import { GlassCard } from "../ui/GlassCard";

export function WorkspaceShell({
  title,
  description,
  aside,
  children,
}: PropsWithChildren<{
  title: string;
  description?: string;
  aside?: ReactNode;
}>) {
  return (
    <div className="space-y-4">
      <GlassCard className="overflow-hidden p-5">
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px] xl:items-start">
          <div className="space-y-1.5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Workspace</p>
            <h1 className="text-2xl font-semibold tracking-tight text-graphite">{title}</h1>
            {description ? <p className="max-w-2xl text-sm leading-6 text-muted">{description}</p> : null}
          </div>
          {aside ? <div>{aside}</div> : null}
        </div>
      </GlassCard>
      {children}
    </div>
  );
}
