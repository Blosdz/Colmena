import { cn } from '../../utils/cn.js';

const toneMap = {
  draft: 'bg-yellowSoft text-yellowDark',
  active: 'bg-turquoiseSoft text-turquoiseDark',
  published: 'bg-turquoiseSoft text-turquoiseDark',
  collecting: 'bg-orangeSoft text-orangeDark',
  results: 'bg-[#eef2ff] text-info',
  report: 'bg-[#eefcf0] text-success',
  neutral: 'bg-[#f3f4f6] text-muted',
};

export function StatusPill({ label, tone = 'neutral' }) {
  return (
    <span className={cn('inline-flex rounded-full px-3 py-1 text-xs font-semibold', toneMap[tone] || toneMap.neutral)}>
      {label}
    </span>
  );
}

export default StatusPill;
