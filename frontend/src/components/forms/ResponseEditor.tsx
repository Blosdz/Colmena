import { Plus, Star, Trash2 } from "lucide-react";

import type { ExogenousOption, ParsedQuestion } from "../../utils/bulkQuestionParser";
import {
  VARIABLE_PRESETS,
  exogenousOptionsFromPreset,
  exogenousTypeFromPreset,
} from "../forms-wizard/scalePresets";
import type { CatalogScale } from "./BulkQuestionTable";
import { cn } from "../../utils/cn";

const EXO_PREFIX = "exo:";
const EXO_CUSTOM = "exo:__custom__";

/** Renderiza la escala tal como la verá el encuestado, según su render_style. */
export function ScalePreviewField({ scale, questionId }: { scale: CatalogScale; questionId: string }) {
  const options = scale.options;
  if (options.length === 0) return null;
  const first = options[0];
  const last = options[options.length - 1];

  switch (scale.render_style) {
    case "slider_line":
      return (
        <div className="max-w-md">
          <input disabled type="range" min={first.value} max={last.value} defaultValue={first.value} className="w-full accent-amber" />
          <div className="flex justify-between text-[10px] text-muted">
            <span>{first.label}</span>
            <span>{last.label}</span>
          </div>
        </div>
      );
    case "nps":
      return (
        <div className="flex flex-wrap items-center gap-1">
          {options.map((opt) => (
            <span key={opt.value} className="flex h-7 w-7 items-center justify-center rounded-md border border-colmena-border bg-white text-[11px] font-semibold text-dark" title={opt.label}>
              {opt.value}
            </span>
          ))}
        </div>
      );
    case "stars":
      return (
        <div className="flex items-center gap-1" title={options.map((o) => o.label).join(" · ")}>
          {options.map((opt) => (
            <Star key={opt.value} className="h-4 w-4 text-amber" />
          ))}
        </div>
      );
    case "faces": {
      const faces = ["😞", "🙁", "😐", "🙂", "😄"];
      return (
        <div className="flex items-center gap-1.5">
          {options.map((opt, i) => (
            <span key={opt.value} className="text-lg" title={opt.label}>
              {faces[Math.min(i, faces.length - 1)]}
            </span>
          ))}
        </div>
      );
    }
    default:
      return (
        <div className="flex flex-wrap gap-1.5">
          {options.map((opt) => (
            <label key={opt.value} className="flex cursor-default items-center gap-1.5 rounded-lg border border-colmena-border bg-white px-2 py-1 text-[11px] text-dark">
              <input disabled name={`preview-${questionId}`} type="radio" />
              {opt.label}
            </label>
          ))}
        </div>
      );
  }
}

const EXO_TYPE_LABEL: Record<NonNullable<ParsedQuestion["exogenousType"]>, string> = {
  single_choice: "Opción única",
  number: "Número",
  text_short: "Texto corto",
};

type Props = {
  question: ParsedQuestion;
  /** Escala efectiva (propia o heredada) cuando responseKind === "scale". */
  effectiveScale?: CatalogScale;
  inherited: boolean;
  scales: CatalogScale[];
  defaultScale?: CatalogScale;
  onUpdate: (updates: Partial<ParsedQuestion>) => void;
};

/**
 * Editor de respuesta modular por ítem: un dropdown elige el "editor" (escala
 * global heredada, otra escala del catálogo, o una **variable exógena** como
 * Sexo con sus propias opciones editables) y debajo se muestra el cuerpo
 * correspondiente. Estilo COLMENA 2.0: el layout es modular, cada tipo trae su
 * propio editor.
 */
export function ResponseEditor({
  question,
  effectiveScale,
  inherited,
  scales,
  defaultScale,
  onUpdate,
}: Props) {
  const isExogenous = question.responseKind === "exogenous";

  const currentValue = question.scale || "";

  const handleSelect = (raw: string) => {
    if (raw.startsWith(EXO_PREFIX)) {
      const presetId = raw.slice(EXO_PREFIX.length);
      const preset = VARIABLE_PRESETS.find((p) => p.id === presetId);
      onUpdate({
        responseKind: "exogenous",
        type: preset ? exogenousTypeFromPreset(preset) : "single_choice",
        dimensionName: "",
        scale: "",
        scored: false,
        reversed: false,
        isImportance: false,
        exogenousType: preset ? exogenousTypeFromPreset(preset) : "single_choice",
        exogenousOptions: preset ? exogenousOptionsFromPreset(preset) : [{ label: "Opción 1", value: 1 }, { label: "Opción 2", value: 2 }],
        text: !question.text && preset ? preset.name : question.text,
      });
      return;
    }
    // Volver a una escala Likert compartida.
    onUpdate({
      responseKind: "scale",
      type: "likert",
      scale: raw,
      scored: true,
      exogenousType: undefined,
      exogenousOptions: undefined,
    });
  };

  const opts = question.exogenousOptions ?? [];
  const setOpts = (next: ExogenousOption[]) => onUpdate({ exogenousOptions: next });
  const updateOpt = (i: number, patch: Partial<ExogenousOption>) =>
    setOpts(opts.map((o, idx) => (idx === i ? { ...o, ...patch } : o)));

  return (
    <div className="question-response-editor">
      <div className="question-response-kind" role="group" aria-label="Tipo de respuesta">
        <button type="button" aria-pressed={!isExogenous} onClick={() => { if (isExogenous) handleSelect(""); }}>Escala Likert</button>
        <button type="button" aria-pressed={isExogenous} onClick={() => { if (!isExogenous) handleSelect(EXO_CUSTOM); }}>Variable exógena</button>
      </div>
      {isExogenous ? <div className="question-preset-list"><span>Empezar con:</span>{VARIABLE_PRESETS.map(p => <button type="button" key={p.id} className="question-button" onClick={() => handleSelect(`${EXO_PREFIX}${p.id}`)}>{p.name}</button>)}</div> : <label className="question-scale-choice">Escala de respuesta
        <select value={currentValue} onChange={e => handleSelect(e.target.value)}><option value="">Compartida{defaultScale ? ` · ${defaultScale.name}` : " · sin definir"}</option>{scales.map(s => <option key={s.id} value={s.name}>{s.name}</option>)}</select>
        <span className="question-helper">{inherited ? "Usa la escala compartida de arriba." : "Esta escala se aplica solo a esta pregunta."}</span>
      </label>}

      {/* Cuerpo modular ── escala Likert */}
      {!isExogenous && effectiveScale && (
        <ScalePreviewField scale={effectiveScale} questionId={question.id} />
      )}

      {/* Cuerpo modular ── variable exógena */}
      {isExogenous && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            {(Object.keys(EXO_TYPE_LABEL) as (keyof typeof EXO_TYPE_LABEL)[]).map((t) => (
              <button
                key={t}
                type="button"
                aria-pressed={(question.exogenousType ?? "single_choice") === t}
                onClick={() => onUpdate({ exogenousType: t, type: t })}
                className={cn(
                  "rounded-md px-2 py-1 text-[10px] font-semibold border transition-colors",
                  (question.exogenousType ?? "single_choice") === t
                    ? "border-amber bg-amber/10 text-amber"
                    : "border-colmena-border text-muted hover:border-amber/40",
                )}
              >
                {EXO_TYPE_LABEL[t]}
              </button>
            ))}
          </div>

          {(question.exogenousType ?? "single_choice") === "single_choice" ? (
            <div className="space-y-1.5">
              {opts.map((opt, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <input
                    className="flex-1 bg-white outline-none border border-colmena-border hover:border-amber focus:border-amber rounded px-2 py-1 text-[11px] text-dark"
                    aria-label={`Etiqueta de opción ${i + 1}`}
                    placeholder={`Opción ${i + 1}`}
                    value={opt.label}
                    onChange={(e) => updateOpt(i, { label: e.target.value })}
                  />
                  <input
                    type="number"
                    className="w-14 bg-white outline-none border border-colmena-border hover:border-amber focus:border-amber rounded px-1.5 py-1 text-[11px] text-dark"
                    aria-label={`Valor de opción ${i + 1}`}
                    title="Valor con el que se guarda esta opción"
                    value={opt.value}
                    onChange={(e) => updateOpt(i, { value: Number(e.target.value) })}
                  />
                  <button
                    type="button"
                    className="p-1 text-muted hover:text-danger"
                    onClick={() => setOpts(opts.filter((_, idx) => idx !== i))}
                    title="Quitar opción"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => setOpts([...opts, { label: "", value: Math.max(0, ...opts.map(o => o.value)) + 1 }])}
                className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber hover:underline"
              >
                <Plus className="w-3 h-3" /> Agregar opción
              </button>
            </div>
          ) : (
            <p className="text-[10px] text-muted">
              {question.exogenousType === "number"
                ? "El participante escribe un número (edad, ingresos, etc.). Se guarda tal cual."
                : "El participante escribe texto libre. No se puntúa ni se compara por categorías."}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
