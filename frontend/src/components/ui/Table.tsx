import type { PropsWithChildren, TableHTMLAttributes } from "react";

import { cn } from "../../utils/cn";

export function TableContainer({ children, className }: PropsWithChildren<{ className?: string }>) {
  return (
    <div className={cn("overflow-hidden rounded-[24px] border border-border bg-white", className)}>
      <div className="overflow-x-auto">{children}</div>
    </div>
  );
}

export function Table({ children, className, ...props }: PropsWithChildren<TableHTMLAttributes<HTMLTableElement>>) {
  return (
    <table className={cn("min-w-full border-collapse text-sm", className)} {...props}>
      {children}
    </table>
  );
}

export function Th({ children, className }: PropsWithChildren<{ className?: string }>) {
  return (
    <th
      className={cn(
        "border-b border-border bg-[#fcfbf7] px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.12em] text-muted",
        className,
      )}
    >
      {children}
    </th>
  );
}

export function Td({ children, className }: PropsWithChildren<{ className?: string }>) {
  return <td className={cn("border-b border-border/70 px-4 py-3 align-top text-dark", className)}>{children}</td>;
}
