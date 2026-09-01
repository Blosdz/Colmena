import { cn } from '../../utils/cn.js';

/**
 * Piezas de tabla compartidas (antes reimplementadas casi idénticas en 6+
 * archivos: mismo `border-collapse text-left text-sm`, mismo padding de
 * celda `px-4 py-2.5/3` copiado y pegado). Un solo lugar decide el chrome
 * de la tabla; cada página sigue siendo dueña de sus columnas y filas.
 */

export function TableContainer({ children, className = '' }) {
  return <div className={cn('overflow-x-auto rounded-2xl border border-border', className)}>{children}</div>;
}

export function Table({ children, className = '' }) {
  return <table className={cn('w-full border-collapse text-left text-sm', className)}>{children}</table>;
}

export function THead({ children, className = '' }) {
  return <thead className={cn('bg-surfaceSoft text-xs font-semibold uppercase tracking-wide text-muted', className)}>{children}</thead>;
}

export function Tr({ children, className = '', ...props }) {
  return (
    <tr className={cn('border-t border-border first:border-t-0', className)} {...props}>
      {children}
    </tr>
  );
}

export function Th({ children, className = '', align = 'left' }) {
  return (
    <th className={cn('whitespace-nowrap px-3 py-2.5', align === 'right' && 'text-right', align === 'center' && 'text-center', className)}>
      {children}
    </th>
  );
}

export function Td({ children, className = '', align = 'left' }) {
  return (
    <td className={cn('px-3 py-2', align === 'right' && 'text-right', align === 'center' && 'text-center', className)}>
      {children}
    </td>
  );
}

export default Table;
