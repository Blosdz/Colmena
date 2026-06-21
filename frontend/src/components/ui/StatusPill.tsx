import { cn } from "../../utils/cn";

const toneMap = {
  draft: "bg-yellowSoft text-yellowDark",
  active: "bg-turquoiseSoft text-turquoiseDark",
  published: "bg-turquoiseSoft text-turquoiseDark",
  collecting: "bg-orangeSoft text-orangeDark",
  results: "bg-[#eef2ff] text-info",
  report: "bg-[#eefcf0] text-success",
  neutral: "bg-[#f3f4f6] text-muted",
} as const;

export function StatusPill({ label, tone = "neutral" }: { label: string; tone?: keyof typeof toneMap }) {
  return (
    <span className={cn("inline-flex rounded-full px-3 py-1 text-xs font-semibold", toneMap[tone])}>{label}</span>
  );
}
