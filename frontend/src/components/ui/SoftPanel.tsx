import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "../../utils/cn";

export function SoftPanel({
  children,
  className,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div
      className={cn("rounded-[24px] border border-border bg-[#fffdf8] p-4 shadow-card", className)}
      {...props}
    >
      {children}
    </div>
  );
}
