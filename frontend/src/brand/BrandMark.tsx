import { cn } from "../utils/cn";

type BrandMarkProps = {
  className?: string;
};

export function BrandMark({ className }: BrandMarkProps) {
  return (
    <svg
      aria-label="Colmena"
      className={cn("h-10 w-10 shrink-0", className)}
      fill="none"
      viewBox="0 0 56 56"
      xmlns="http://www.w3.org/2000/svg"
    >
      <polygon
        points="16,4 25,9 24,20 14,23 7,16 8,8"
        stroke="#F5B21A"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.8"
      />
      <polygon
        points="31,8 40,6 48,13 47,23 36,25 29,17"
        stroke="#FF6A2A"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.8"
      />
      <polygon
        points="23,24 32,22 39,29 38,40 27,43 20,35"
        stroke="#11B7B2"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.8"
      />
    </svg>
  );
}
