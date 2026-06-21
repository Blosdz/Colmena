import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "../../utils/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padded?: boolean;
}

export function Card({ children, className, padded = true, ...props }: PropsWithChildren<CardProps>) {
  return (
    <div
      className={cn(
        "rounded-[28px] border border-border bg-surface shadow-card",
        padded && "p-6",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
