import { useEffect, useRef, useState } from "react";
import { Palette } from "lucide-react";

interface ChartColorPickerProps {
  labels: string[];
  colors: string[];
  onSave: (colors: string[]) => void;
  onReset: () => void;
  isSaving?: boolean;
  isCustom?: boolean;
}

/**
 * Selector de color por barra: un panel flotante con un `<input type="color">`
 * por categoría, para que el usuario fije a mano el color de cada barra del
 * gráfico (persistido por el llamador vía `onSave`/`onReset`).
 */
export function ChartColorPicker({
  labels,
  colors,
  onSave,
  onReset,
  isSaving = false,
  isCustom = false,
}: ChartColorPickerProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<string[]>(colors);
  const containerRef = useRef<HTMLDivElement>(null);

  // Cierra el panel al hacer click fuera, igual que los demás flotantes del proyecto.
  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  function toggleOpen() {
    if (!open) setDraft(colors);
    setOpen((current) => !current);
  }

  function handleSave() {
    onSave(draft);
    setOpen(false);
  }

  function handleReset() {
    onReset();
    setOpen(false);
  }

  if (colors.length === 0) return null;

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-label="Colores del gráfico"
        title="Colores del gráfico"
        aria-pressed={open}
        onClick={toggleOpen}
        className={`inline-flex h-8 w-8 items-center justify-center rounded-[10px] transition-colors ${
          open ? "bg-white text-dark shadow-sm" : "text-muted hover:text-dark"
        }`}
      >
        <Palette className="h-4 w-4" />
      </button>

      {open ? (
        <div className="animate-colmena-fade-in absolute right-0 top-full z-20 mt-2 w-56 rounded-[14px] border border-border bg-white p-3 shadow-glass">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.06em] text-muted">
            Colores del gráfico
          </p>
          <div className="space-y-2">
            {labels.map((label, index) => (
              <label key={`${label}-${index}`} className="flex items-center gap-2">
                <input
                  type="color"
                  className="h-4 w-4 shrink-0 cursor-pointer rounded-full border-0 bg-transparent p-0"
                  value={draft[index] ?? "#000000"}
                  onChange={(event) =>
                    setDraft((current) => {
                      const next = [...current];
                      next[index] = event.target.value;
                      return next;
                    })
                  }
                />
                <span className="truncate text-xs text-dark" title={label}>
                  {label}
                </span>
              </label>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-end gap-2">
            <button
              type="button"
              className="colmena-button-sm-secondary"
              onClick={handleReset}
              disabled={!isCustom}
            >
              Restablecer
            </button>
            <button
              type="button"
              className="colmena-button-sm-primary"
              onClick={handleSave}
              disabled={isSaving}
            >
              Guardar
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
