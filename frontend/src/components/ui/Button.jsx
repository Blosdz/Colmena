import { cn } from '../../utils/cn.js';

const variantStyles = {
  primary: 'bg-dark text-white hover:bg-black/90',
  secondary: 'bg-surfaceSoft text-dark hover:bg-[#f9edd0]',
  ghost: 'bg-transparent text-muted hover:bg-black/5',
  danger: 'bg-danger text-white hover:bg-danger/90',
};

const sizeStyles = {
  xs: 'h-7 rounded-lg px-2.5 text-xs',
  sm: 'h-8 rounded-lg px-3 text-xs',
  md: 'h-10 rounded-xl px-4 text-sm',
  lg: 'h-11 rounded-xl px-5 text-sm',
};

export function Button({
  children,
  className = '',
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  ...props
}) {
  return (
    <button
      className={cn(
        'inline-flex shrink-0 items-center justify-center gap-1.5 font-semibold transition focus:outline-none focus:ring-2 focus:ring-amber/30 disabled:cursor-not-allowed disabled:opacity-60',
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? 'Procesando...' : children}
    </button>
  );
}

export default Button;
