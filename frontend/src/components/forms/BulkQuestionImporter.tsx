import { FileSpreadsheet } from "lucide-react";
import { useCallback, useState } from "react";
import { parseBulkQuestions, type ParsedQuestion } from "../../utils/bulkQuestionParser";

type Props = {
  onDataParsed: (rows: ParsedQuestion[]) => void;
};

export function BulkQuestionImporter({ onDataParsed }: Props) {
  const [count, setCount] = useState(0);

  const handlePaste = useCallback(
    (event: React.ClipboardEvent<HTMLDivElement>) => {
      const pastedText = event.clipboardData.getData("text");
      if (!pastedText) return;
      const parsedRows = parseBulkQuestions(pastedText);
      if (parsedRows.length > 0) {
        onDataParsed(parsedRows);
        setCount(prev => prev + parsedRows.length);
      }
    },
    [onDataParsed]
  );

  return (
    <div className="flex items-center gap-2 rounded-lg border border-dashed border-colmena-border bg-white px-3 py-2 transition-colors focus-within:border-amber focus-within:ring-2 focus-within:ring-amber/10">
      <FileSpreadsheet className="w-4 h-4 text-amber shrink-0" />
      <div
        className="flex-1 min-h-[28px] text-[12px] text-muted outline-none cursor-text"
        contentEditable
        onPaste={handlePaste}
        data-placeholder="Pega tus ítems desde Excel aquí (Ctrl+V)..."
        style={{ WebkitUserModify: "read-write-plaintext-only" } as React.CSSProperties}
      />
      {count > 0 && (
        <span className="shrink-0 text-[10px] font-bold text-success bg-success/10 rounded px-1.5 py-0.5">
          +{count}
        </span>
      )}
    </div>
  );
}
