import { useMemo } from 'react';
import { flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table';

import { EmptyState } from '../../ui/EmptyState.jsx';
import { displayLabel } from '../../../utils/labels.js';

const columns = [
  { accessorKey: 'item_code', header: 'Ítem' },
  { accessorKey: 'question_text', header: 'Pregunta' },
  { accessorKey: 'research_variable_name', header: 'Variable', cell: (info) => info.getValue() || '—' },
  { accessorKey: 'dimension_name', header: 'Dimensión', cell: (info) => info.getValue() || 'Pregunta directa' },
  { accessorKey: 'subdimension_name', header: 'Subdimensión', cell: (info) => info.getValue() || '—' },
  { accessorKey: 'weight', header: 'Peso' },
  { accessorKey: 'scoring_direction', header: 'Dirección', cell: (info) => info.getValue() ? displayLabel(info.getValue()) : '—' },
  { accessorKey: 'status', header: 'Estado', cell: (info) => displayLabel(info.getValue()) },
];

export default function InstrumentMatrixView({ matrix }) {
  const data = useMemo(() => matrix.rows, [matrix.rows]);
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() });

  if (data.length === 0) {
    return <EmptyState title="Sin preguntas asignadas" description="Selecciona una variable y agrega preguntas directas o preguntas dentro de sus dimensiones." />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="bg-surfaceSoft">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="border-b border-r border-border px-4 py-2.5 text-[11px] font-bold uppercase tracking-[0.06em] text-muted last:border-r-0"
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="transition hover:bg-[#fafbfc]">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="border-b border-r border-border px-4 py-2.5 text-dark last:border-r-0">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
