import { cn } from "../../utils/cn";

export interface TabItem {
  value: string;
  label: string;
}

interface TabsProps {
  items: TabItem[];
  value: string;
  onValueChange: (value: string) => void;
}

export function Tabs({ items, value, onValueChange }: TabsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => {
        const isActive = item.value === value;
        return (
          <button
            key={item.value}
            className={cn(
              "rounded-full px-4 py-2 text-sm font-medium transition",
              isActive ? "bg-dark text-white shadow-soft" : "bg-surfaceSoft text-muted hover:text-dark",
            )}
            onClick={() => onValueChange(item.value)}
            type="button"
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
