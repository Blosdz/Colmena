import { Inbox } from "lucide-react";
import type { PropsWithChildren } from "react";

export function EmptyState({
  title,
  description,
  children,
}: PropsWithChildren<{ title: string; description: string }>) {
  return (
    <div className="animate-colmena-fade-in rounded-2xl border border-dashed border-[#dfe2e6] bg-gradient-to-b from-[#fafbfc] to-white px-8 py-12 text-center">
      <div className="mx-auto max-w-sm space-y-4">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f5f6f8] text-muted/40">
          <Inbox className="h-7 w-7" />
        </div>
        <div className="space-y-2">
          <h3 className="text-[16px] font-semibold text-dark">{title}</h3>
          <p className="text-[13px] leading-6 text-muted">{description}</p>
        </div>
        {children && <div className="pt-2">{children}</div>}
      </div>
    </div>
  );
}
