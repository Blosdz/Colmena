import { Upload, FileSpreadsheet, X, Check } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import * as XLSX from "xlsx";
import type { DataRow } from "../../utils/projectDraftStore";

type Props = {
  columns: string[];
  rows: DataRow[];
  onDataLoaded: (columns: string[], rows: DataRow[]) => void;
};

export function ExcelDataUploader({ columns, rows, onDataLoaded }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");

  const handleFile = useCallback((file: File) => {
    setError("");
    setFileName(file.name);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: "array" });
        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];
        const json = XLSX.utils.sheet_to_json<DataRow>(sheet, { defval: "" });

        if (json.length === 0) {
          setError("El archivo no contiene datos.");
          return;
        }

        const cols = Object.keys(json[0]);
        onDataLoaded(cols, json);
      } catch {
        setError("Error al leer el archivo. Asegúrate de que sea .xlsx o .csv válido.");
      }
    };
    reader.readAsArrayBuffer(file);
  }, [onDataLoaded]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const hasData = rows.length > 0;

  return (
    <div className="space-y-4">
      {/* Upload zone */}
      {!hasData && (
        <div
          className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-colmena-border py-5 px-5 bg-white hover:border-amber/40 hover:bg-amber/3 transition-all cursor-pointer"
          onClick={() => fileRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber/10 text-amber">
            <Upload className="w-5 h-5" />
          </div>
          <div className="text-center">
            <p className="text-[13px] font-semibold text-dark">Sube tu base de datos (.xlsx, .csv)</p>
            <p className="text-[11px] text-muted mt-1">Arrastra aquí o haz clic para seleccionar</p>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx,.xls,.csv"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
          />
        </div>
      )}

      {error && (
        <div className="text-[11px] text-danger bg-danger/5 border border-danger/10 rounded-lg px-3 py-2">{error}</div>
      )}

      {/* Data loaded summary + preview */}
      {hasData && (
        <div className="space-y-3">
          {/* File info bar */}
          <div className="flex items-center gap-3 rounded-xl border border-colmena-border bg-white px-4 py-2.5">
            <FileSpreadsheet className="w-4 h-4 text-success shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="text-[12px] font-semibold text-dark truncate block">{fileName}</span>
              <span className="text-[10px] text-muted">{rows.length} registros · {columns.length} columnas</span>
            </div>
            <span className="shrink-0 flex items-center gap-1 text-[10px] font-bold text-success bg-success/10 rounded px-2 py-0.5">
              <Check className="w-3 h-3" /> Cargado
            </span>
            <button
              className="shrink-0 p-1 text-muted hover:text-danger transition-colors"
              onClick={() => { onDataLoaded([], []); setFileName(""); }}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Data preview table */}
          <div className="rounded-xl border border-colmena-border bg-white overflow-hidden">
            <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
              <table className="min-w-full text-[11px]">
                <thead className="bg-colmena-bg sticky top-0">
                  <tr>
                    <th className="px-2 py-1.5 text-left font-bold uppercase tracking-[0.06em] text-muted border-b border-colmena-border">#</th>
                    {columns.slice(0, 25).map((col) => (
                      <th key={col} className="px-2 py-1.5 text-left font-bold uppercase tracking-[0.06em] text-muted border-b border-colmena-border whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                    {columns.length > 25 && (
                      <th className="px-2 py-1.5 text-left font-bold text-muted border-b border-colmena-border">+{columns.length - 25}</th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-colmena-border">
                  {rows.slice(0, 20).map((row, i) => (
                    <tr key={i} className="hover:bg-amber/3 transition-colors">
                      <td className="px-2 py-1 text-muted font-medium">{i + 1}</td>
                      {columns.slice(0, 25).map((col) => (
                        <td key={col} className="px-2 py-1 text-dark whitespace-nowrap">{String(row[col] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {rows.length > 20 && (
              <div className="px-3 py-1.5 border-t border-colmena-border bg-colmena-bg text-[10px] text-muted">
                Mostrando 20 de {rows.length} registros
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
