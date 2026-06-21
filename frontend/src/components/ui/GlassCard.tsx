import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "../../utils/cn";

export function GlassCard({
  children,
  className,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div
      className={cn(
        "rounded-[26px] border border-white/75 bg-white/78 p-6 shadow-[0_14px_36px_rgba(28,31,36,0.06)] backdrop-blur-md",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
