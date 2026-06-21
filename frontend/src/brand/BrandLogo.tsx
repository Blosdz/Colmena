import { BrandMark } from "./BrandMark";
import { cn } from "../utils/cn";

type BrandLogoProps = {
  className?: string;
  compact?: boolean;
};

export function BrandLogo({ className, compact = false }: BrandLogoProps) {
  if (compact) {
    return <BrandMark className={cn("h-8 w-8", className)} />;
  }

  return (
    <div className={cn("flex h-[32px] items-center gap-3 overflow-visible", className)}>
      <BrandMark className="h-[32px] w-[32px] shrink-0" />
      <div className="flex flex-col justify-center">
        <div className="flex items-center gap-[2px] text-[15px] font-bold tracking-[0.1em] text-[#111111] leading-none">
          <span>COLM</span>
          <span className="flex flex-col gap-[2px] mt-[-1px]">
            <span className="block h-[3px] w-[12px] rounded-full bg-[#F5B21A]" />
            <span className="block h-[3px] w-[12px] rounded-full bg-[#FF6A2A]" />
            <span className="block h-[3px] w-[12px] rounded-full bg-[#11B7B2]" />
          </span>
          <span>NA</span>
        </div>
      </div>
    </div>
  );
}
