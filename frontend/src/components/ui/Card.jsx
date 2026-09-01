import { cn } from '../../utils/cn.js';

const paddingStyles = {
  compact: 'p-3 sm:p-4',
  default: 'p-4 sm:p-5',
  roomy: 'p-5 sm:p-6',
};

export function Card({ children, className = '', padded = true, padding = 'default', ...props }) {
  return (
    <div
      className={cn(
        'rounded-2xl border border-border bg-surface shadow-card',
        padded && (paddingStyles[padding] || paddingStyles.default),
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export default Card;
