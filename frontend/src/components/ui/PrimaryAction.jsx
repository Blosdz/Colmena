import { Button } from './Button.jsx';

export function PrimaryAction({ children, className = '', ...props }) {
  return (
    <Button
      className={`h-12 rounded-2xl bg-gradient-to-r from-amber to-[#ff8d4d] px-5 text-white shadow-soft hover:opacity-95 ${className}`}
      {...props}
    >
      {children}
    </Button>
  );
}

export default PrimaryAction;
