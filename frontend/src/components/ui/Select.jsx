import { cn } from '../../utils/cn.js';

export function Select({ className = '', children, ...props }) {
  return (
    <select
      className={cn(
        'colmena-select h-11 w-full rounded-2xl border border-border bg-white px-4 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20 dark:border-white/10 dark:bg-[#20242b] dark:text-gray-100',
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}

export function SelectOption({ children, ...props }) {
  return <option {...props}>{children}</option>;
}

export default Select;
