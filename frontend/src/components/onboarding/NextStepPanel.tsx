import type { ReactNode } from "react";

import { SoftPanel } from "../ui/SoftPanel";

export function NextStepPanel({
  title = "Proximo paso",
  description,
  items,
  action,
}: {
  title?: string;
  description?: string;
  items?: string[];
  action?: ReactNode;
}) {
  return (
    <SoftPanel className="space-y-3">
      <h3 className="text-sm font-semibold text-dark">{title}</h3>
      {description ? <p className="text-sm leading-6 text-muted">{description}</p> : null}
      {items?.length ? (
        <ul className="space-y-2 text-sm leading-6 text-dark">
          {items.map((item) => (
            <li className="flex gap-2" key={item}>
              <span className="mt-2 h-1.5 w-1.5 rounded-full bg-amber" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {action ? <div className="pt-2">{action}</div> : null}
    </SoftPanel>
  );
}
