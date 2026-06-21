import type { ScoreBand } from "../../types/scoring";
import { formatNumber } from "../../utils/formatters";
import { EmptyState } from "../ui/EmptyState";

export function ScoreBandEditor({ bands }: { bands: ScoreBand[] }) {
  if (bands.length === 0) {
    return (
      <EmptyState
        title="Sin baremos configurados"
        description="Agrega rangos interpretativos para clasificar los puntajes del instrumento."
      />
    );
  }

  return (
    <div className="space-y-2">
      {bands.map((band) => (
        <div className="grid gap-2 rounded-2xl border border-border bg-[#fffdf8] px-4 py-3 md:grid-cols-[160px_140px_minmax(220px,1fr)]" key={band.id}>
          <div>
            <p className="text-sm font-semibold text-dark">{band.label}</p>
            <p className="text-xs uppercase tracking-[0.12em] text-muted">{band.code || "sin codigo"}</p>
          </div>
          <div className="text-sm text-dark">
            {formatNumber(band.min_value)} a {formatNumber(band.max_value)}
          </div>
          <p className="text-sm text-muted">{band.interpretation || "Sin interpretacion breve."}</p>
        </div>
      ))}
    </div>
  );
}
