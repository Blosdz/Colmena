import { useMemo } from "react";
import { ShieldAlert } from "lucide-react";

import type { BaremoResolvedLevel, VariableBaremo } from "../../types/scoring";

/**
 * Vista de lectura de los baremos, al estilo de COLMENA 2.0: por cada variable /
 * dimensión, una barra apilada con el % de participantes en cada nivel y una
 * tabla-resumen (n, puntaje medio, nivel promedio). Todo se deriva de
 * `GET /forms/{id}/scoring/baremos/resolution`; no edita nada.
 */

const SEVERITY_PALETTE_3 = ["#E5484D", "#F5B21A", "#2FA84F"];
const SEVERITY_PALETTE_N = ["#E5484D", "#F2900D", "#F5B21A", "#7AB648", "#2FA84F", "#2563EB", "#7C3AED"];

function sortedLevels(levels: BaremoResolvedLevel[]): BaremoResolvedLevel[] {
  return [...levels].sort((a, b) => a.severity_order - b.severity_order);
}

function levelColor(index: number, count: number): string {
  if (count === 3) return SEVERITY_PALETTE_3[index] ?? SEVERITY_PALETTE_N[index] ?? "#94A3B8";
  return SEVERITY_PALETTE_N[Math.round((index / Math.max(1, count - 1)) * (SEVERITY_PALETTE_N.length - 1))];
}

function fmt(value: number | null | undefined, digits = 1): string {
  return value === null || value === undefined || Number.isNaN(value) ? "—" : value.toFixed(digits);
}

function VariableCard({ item, dense }: { item: VariableBaremo; dense?: boolean }) {
  const levels = sortedLevels(item.levels);
  const colorFor = (i: number) => levelColor(i, levels.length);
  const meanBadgeColor = useMemo(() => {
    const i = levels.findIndex((l) => l.label === item.mean_level);
    return i >= 0 ? colorFor(i) : "#94A3B8";
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.mean_level, levels]);

  const suppressed = item.valid_n === 0;

  return (
    <div className={`rounded-2xl border border-border bg-white ${dense ? "p-4" : "p-5"}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className={`font-semibold text-dark ${dense ? "text-sm" : "text-base"}`}>
            {dense ? "↳ " : ""}
            {item.variable_label}
          </p>
          <p className="text-xs text-muted">
            {item.scoring_level === "dimension" ? "Dimensión" : "Variable"} · fuente del baremo:{" "}
            {item.baremo_source}
          </p>
        </div>
        <div className="flex items-center gap-4 text-right">
          <div>
            <p className="text-[11px] uppercase tracking-wide text-muted">n</p>
            <p className="text-sm font-semibold text-dark tabular-nums">{item.valid_n}</p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-muted">Puntaje</p>
            <p className="text-sm font-semibold text-dark tabular-nums">
              {fmt(item.mean_score)}
              {item.sd_score != null ? ` ± ${fmt(item.sd_score)}` : ""}
            </p>
          </div>
          {item.mean_level ? (
            <span
              className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold text-white"
              style={{ background: meanBadgeColor }}
            >
              {item.mean_level}
            </span>
          ) : null}
        </div>
      </div>

      {suppressed ? (
        <p className="mt-3 inline-flex items-center gap-1.5 text-xs text-muted">
          <ShieldAlert size={13} /> Sin respuestas válidas para clasificar todavía.
        </p>
      ) : (
        <>
          <div className="mt-4 flex h-7 w-full overflow-hidden rounded-lg">
            {levels.map((level, i) => (
              <div
                key={level.label}
                className="flex items-center justify-center text-[11px] font-bold text-white"
                style={{ width: `${level.percent}%`, background: colorFor(i) }}
                title={`${level.label}: ${level.n} (${level.percent.toFixed(1)}%)`}
              >
                {level.percent >= 9 ? `${level.percent.toFixed(0)}%` : ""}
              </div>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
            {levels.map((level, i) => (
              <span key={level.label} className="inline-flex items-center gap-1.5 text-xs text-muted">
                <span className="h-2.5 w-2.5 rounded-sm" style={{ background: colorFor(i) }} />
                <span className="text-dark">{level.label}</span>
                <span className="tabular-nums">
                  {level.n} ({level.percent.toFixed(1)}%)
                </span>
                <span className="text-muted/70">
                  · {fmt(level.min_value, 0)}–{fmt(level.max_value, 0)}
                </span>
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-border bg-white p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1.5 text-lg font-bold text-dark tabular-nums">{value}</p>
    </div>
  );
}

export function BaremoDistributionPanel({ items }: { items: VariableBaremo[] }) {
  const variables = items.filter((i) => i.scoring_level !== "dimension");
  const dimensions = items.filter((i) => i.scoring_level === "dimension");
  const maxN = items.reduce((m, i) => Math.max(m, i.valid_n), 0);

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-white px-4 py-8 text-center text-sm text-muted">
        Aún no hay baremos definidos. Configúralos al crear el proyecto (paso «Baremos») o abajo,
        en las tablas por variable.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Metric label="Respuestas clasificadas" value={maxN} />
        <Metric label="Variables con baremo" value={variables.length} />
        <Metric label="Dimensiones con baremo" value={dimensions.length} />
        <Metric label="Niveles" value={items[0]?.levels.length ?? 0} />
      </div>

      <div className="grid gap-3 xl:grid-cols-2">
        {variables.map((item) => (
          <VariableCard key={item.scoring_config_id} item={item} />
        ))}
      </div>

      {dimensions.length > 0 ? (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-dark">Por dimensión</p>
          <div className="grid gap-3 xl:grid-cols-2">
            {dimensions.map((item) => (
              <VariableCard key={item.scoring_config_id} item={item} dense />
            ))}
          </div>
        </div>
      ) : null}

      <p className="text-xs leading-5 text-muted">
        Las barras muestran distribución, no causalidad. Cada color se acompaña siempre de su
        etiqueta y porcentaje.
      </p>
    </div>
  );
}
