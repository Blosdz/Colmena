import type { OptionHTMLAttributes, PropsWithChildren, SelectHTMLAttributes } from "react";

import { cn } from "../../utils/cn";

export function Select({ className, children, ...props }: PropsWithChildren<SelectHTMLAttributes<HTMLSelectElement>>) {
  return (
    <select
      className={cn(
        "h-11 w-full rounded-2xl border border-border bg-white px-4 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}

export function SelectOption({ children, ...props }: PropsWithChildren<OptionHTMLAttributes<HTMLOptionElement>>) {
  return <option {...props}>{children}</option>;
}
