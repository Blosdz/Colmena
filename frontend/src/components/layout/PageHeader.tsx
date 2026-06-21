import type { PropsWithChildren, ReactNode } from "react";

import { StatusPill } from "../ui/StatusPill";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: PropsWithChildren<{
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}>) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between animate-colmena-fade-in">
      <div className="space-y-2">
        {eyebrow ? <StatusPill label={eyebrow} tone="draft" /> : null}
        <div className="space-y-1.5">
          <h1 className="text-[28px] font-bold tracking-tight text-dark">{title}</h1>
          {description ? (
            <p className="max-w-xl text-[14px] leading-6 text-muted">{description}</p>
          ) : null}
        </div>
      </div>
      {actions ? (
        <div className="flex flex-wrap items-center gap-2.5">{actions}</div>
      ) : null}
    </div>
  );
}
