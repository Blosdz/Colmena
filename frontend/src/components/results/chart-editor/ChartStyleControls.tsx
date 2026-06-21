import type { ChartThemeName } from "../../../types/chartEditor";
import { Select, SelectOption } from "../../ui/Select";
import { ChartPresetSelector } from "./ChartPresetSelector";

export function ChartStyleControls({
  theme,
  orientation,
  labelRotation,
  fontScale,
  showGrid,
  allowOrientation,
  onThemeChange,
  onOrientationChange,
  onLabelRotationChange,
  onFontScaleChange,
  onShowGridChange,
}: {
  theme: ChartThemeName;
  orientation: "vertical" | "horizontal";
  labelRotation: number;
  fontScale: number;
  showGrid: boolean;
  allowOrientation: boolean;
  onThemeChange: (value: ChartThemeName) => void;
  onOrientationChange: (value: "vertical" | "horizontal") => void;
  onLabelRotationChange: (value: number) => void;
  onFontScaleChange: (value: number) => void;
  onShowGridChange: (value: boolean) => void;
}) {
  return (
    <div className="space-y-4">
      <ChartPresetSelector value={theme} onChange={onThemeChange} />

      <div className="space-y-3 rounded-2xl border border-border bg-[#fcfbf7] p-4">
        <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Estilo</h4>

        {allowOrientation ? (
          <div className="space-y-2">
            <label className="text-sm font-medium text-dark">Orientacion</label>
            <Select value={orientation} onChange={(event) => onOrientationChange(event.target.value as "vertical" | "horizontal")}>
              <SelectOption value="vertical">Vertical</SelectOption>
              <SelectOption value="horizontal">Horizontal</SelectOption>
            </Select>
          </div>
        ) : null}

        <div className="space-y-2">
          <label className="text-sm font-medium text-dark">Rotacion de etiquetas ({labelRotation}°)</label>
          <input
            className="w-full accent-amber"
            max={90}
            min={-30}
            onChange={(event) => onLabelRotationChange(Number(event.target.value))}
            type="range"
            value={labelRotation}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-dark">Escala de fuente ({fontScale.toFixed(1)}x)</label>
          <input
            className="w-full accent-amber"
            max={1.6}
            min={0.8}
            onChange={(event) => onFontScaleChange(Number(event.target.value))}
            step={0.1}
            type="range"
            value={fontScale}
          />
        </div>

        <label className="flex items-center gap-3 text-sm text-dark">
          <input
            checked={showGrid}
            className="h-4 w-4 accent-amber"
            onChange={(event) => onShowGridChange(event.target.checked)}
            type="checkbox"
          />
          Mostrar grilla
        </label>
      </div>
    </div>
  );
}
