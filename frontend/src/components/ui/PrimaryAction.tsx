import type { PropsWithChildren } from "react";

import { Button } from "./Button";

export function PrimaryAction({
  children,
  ...props
}: PropsWithChildren<React.ComponentProps<typeof Button>>) {
  return (
    <Button
      className="h-12 rounded-2xl bg-gradient-to-r from-amber to-[#ff8d4d] px-5 text-white shadow-soft hover:opacity-95"
      {...props}
    >
      {children}
    </Button>
  );
}
