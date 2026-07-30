import { useMemo, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { ScaleDraft } from "../../utils/projectDraftStore";
import type { CatalogScale } from "./BulkQuestionTable";

type Props = {
  scale: ScaleDraft;
  onChange: (scale: ScaleDraft) => void;
  /** Catálogo de escalas del backend (presets de sistema + del proyecto), fuente única de verdad */
  presets: CatalogScale[];
  /** Primer ítem real de la variable, para que el preview use una pregunta verdadera */
  previewQuestion?: string;
  /** Modo embebido (dentro del panel de Ítems): usa todo el ancho y oculta el encabezado propio */
  embedded?: boolean;
};

/** Copy de presentación por tipo de escala: pregunta de ejemplo y explicación de cuándo usarla.
 *  Esto es texto de ayuda de la UI, no contenido del instrumento — las etiquetas/valores reales
 *  siempre vienen del catálogo del backend (`presets`), nunca de aquí. */
const KIND_META: Record<string, { label: string; question: string; hint: string }> = {
  frecuencia: {
    label: "Frecuencia",
    question: "¿Con qué frecuencia siente dolor?",
    hint: "Para conductas o síntomas que se repiten",
  },
  intensidad: {
    label: "Intensidad",
    question: "¿Qué tan intenso es su dolor?",
    hint: "Para la gravedad de un síntoma",
  },
  acuerdo: {
    label: "Acuerdo",
    question: "Mi dolor interfiere en mi vida diaria",
    hint: "Para actitudes, creencias u opiniones",
  },
  dificultad: {
    label: "Dificultad",
    question: "¿Puede usted subir escaleras?",
    hint: "Para capacidad funcional",
  },
  satisfaccion: {
    label: "Satisfacción",
    question: "¿Qué tan satisfecho está con el servicio?",
    hint: "Para percepción de calidad o servicio",
  },
};
const FALLBACK_KIND_META = { label: "Escala", question: "Pregunta de ejemplo", hint: "" };

const LABEL_CLS = "block text-[10px] font-bold text-gray-500 uppercase mb-2";

/** Detecta el tipo/puntos activos a partir del id real guardado en la escala (no por texto). */
function detectPreset(
  scale: ScaleDraft,
  systemPresets: CatalogScale[],
): { key: string; points: number } {
  if (scale.catalogScaleId) {
    const match = systemPresets.find((p) => p.id === scale.catalogScaleId);
    if (match?.scale_kind && match.points) {
      return { key: match.scale_kind, points: match.points };
    }
  }
  return { key: "personalizada", points: scale.options.length || 5 };
}

export function ScaleBuilder({ scale, onChange, presets, previewQuestion, embedded = false }: Props) {
  const systemPresets = useMemo(() => presets.filter((p) => p.project_id == null), [presets]);

  const byKind = useMemo(() => {
    const map = new Map<string, Map<number, CatalogScale>>();
    systemPresets.forEach((p) => {
      if (!p.scale_kind || p.scale_kind === "personalizada" || !p.points) return;
      if (!map.has(p.scale_kind)) map.set(p.scale_kind, new Map());
      map.get(p.scale_kind)!.set(p.points, p);
    });
    return map;
  }, [systemPresets]);

  const kinds = useMemo(() => Array.from(byKind.keys()), [byKind]);

  const detected = useMemo(() => detectPreset(scale, systemPresets), [scale, systemPresets]);
  const [selectedKey, setSelectedKey] = useState<string>(detected.key);
  const [points, setPoints] = useState<number>(detected.points);
  const [previewValue, setPreviewValue] = useState<number | null>(null);

  const pointsForSelectedKind = useMemo(
    () => (byKind.has(selectedKey) ? Array.from(byKind.get(selectedKey)!.keys()).sort((a, b) => a - b) : []),
    [byKind, selectedKey],
  );

  const applyPreset = (key: string, pts: number) => {
    setSelectedKey(key);
    setPoints(pts);
    setPreviewValue(null);
    const catalogScale = byKind.get(key)?.get(pts);
    if (!catalogScale) return; // "personalizada" u opción sin ese punto sembrado: conserva lo actual
    onChange({
      name: catalogScale.name,
      options: catalogScale.options.map((o, i) => ({ id: String(i + 1), value: o.value, label: o.label })),
      catalogScaleId: catalogScale.id,
    });
  };

  const selectCustom = () => {
    setSelectedKey("personalizada");
    setPreviewValue(null);
  };

  const handleLabelEdit = (optionId: string, label: string) => {
    onChange({
      ...scale,
      options: scale.options.map((o) => (o.id === optionId ? { ...o, label } : o)),
      catalogScaleId: null,
    });
  };

  const handleValueEdit = (optionId: string, value: number) => {
    onChange({
      ...scale,
      options: scale.options.map((o) => (o.id === optionId ? { ...o, value } : o)),
      catalogScaleId: null,
    });
  };

  const addOption = () => {
    const nextValue =
      scale.options.length > 0 ? Math.max(...scale.options.map((o) => o.value)) + 1 : 1;
    onChange({
      ...scale,
      name: scale.name || "Personalizada",
      options: [...scale.options, { id: crypto.randomUUID(), value: nextValue, label: "" }],
      catalogScaleId: null,
    });
  };

  const removeOption = (optionId: string) => {
    onChange({ ...scale, options: scale.options.filter((o) => o.id !== optionId), catalogScaleId: null });
  };

  const isCustom = selectedKey === "personalizada";
  const activeMeta = KIND_META[selectedKey] ?? FALLBACK_KIND_META;

  const previewText = previewQuestion?.trim() || activeMeta.question;

  return (
    <div
      className={embedded ? "w-full px-4 py-5" : "max-w-[1000px] mx-auto px-8 py-12"}
      data-purpose="scale-definition"
    >
      {/* Encabezado (oculto en modo embebido: el panel de Ítems ya lo titula) */}
      {!embedded && (
        <div className="flex items-start gap-4 mb-8">
          <div className="mt-1 text-2xl text-colmena-orange">☰</div>
          <div>
            <h1 className="text-lg font-bold text-gray-800">Escala de respuesta</h1>
            <p className="text-sm text-gray-400">
              Todos los ítems de esta variable usarán la misma escala. Elige el tipo según lo que mide tu
              instrumento.
            </p>
          </div>
        </div>
      )}

      <div className={embedded ? "grid grid-cols-12 gap-6" : "grid grid-cols-12 gap-8"}>
        {/* ── Columna izquierda: selección ── */}
        <div className="col-span-7 space-y-8">
          {/* Nombre de la escala: editable siempre, incluso partiendo de un preset */}
          <div>
            <label className={LABEL_CLS}>Nombre de la escala</label>
            <input
              className="w-full p-2.5 border border-gray-200 rounded-lg focus:ring-colmena-orange focus:border-colmena-orange bg-gray-50/30 outline-none transition text-sm"
              type="text"
              placeholder="Ej. Escala de frecuencia"
              value={scale.name}
              onChange={(e) => onChange({ ...scale, name: e.target.value, catalogScaleId: null })}
              onBlur={(e) => {
                if (!e.target.value.trim()) onChange({ ...scale, name: "Personalizada", catalogScaleId: null });
              }}
            />
          </div>

          {/* Tipo de escala: tarjetas radiales, generadas desde el catálogo del backend */}
          <div>
            <label className={LABEL_CLS}>Tipo de escala</label>
            <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label="Tipo de escala">
              {kinds.map((kind) => {
                const meta = KIND_META[kind] ?? FALLBACK_KIND_META;
                const active = selectedKey === kind;
                const kindPoints = Array.from(byKind.get(kind)!.keys()).sort((a, b) => a - b);
                const defaultPts = kindPoints.includes(points) ? points : kindPoints[0];
                return (
                  <button
                    key={kind}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    onClick={() => applyPreset(kind, defaultPts)}
                    className={`text-left p-4 rounded-lg border transition-colors ${
                      active
                        ? "border-colmena-orange bg-colmena-orange/5 ring-1 ring-colmena-orange"
                        : "border-gray-200 bg-gray-50/30 hover:border-colmena-orange/40"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`w-3.5 h-3.5 rounded-full border-2 shrink-0 ${
                          active ? "border-colmena-orange bg-colmena-orange" : "border-gray-300"
                        }`}
                      />
                      <span className="text-sm font-bold text-gray-800">{meta.label}</span>
                    </div>
                    <p className="text-xs text-gray-500 italic">"{meta.question}"</p>
                    <p className="text-[10px] text-gray-400 mt-1">{meta.hint}</p>
                  </button>
                );
              })}

              {/* Personalizada */}
              <button
                type="button"
                role="radio"
                aria-checked={selectedKey === "personalizada"}
                onClick={selectCustom}
                className={`text-left p-4 rounded-lg border transition-colors ${
                  selectedKey === "personalizada"
                    ? "border-colmena-orange bg-colmena-orange/5 ring-1 ring-colmena-orange"
                    : "border-gray-200 bg-gray-50/30 hover:border-colmena-orange/40"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`w-3.5 h-3.5 rounded-full border-2 shrink-0 ${
                      selectedKey === "personalizada"
                        ? "border-colmena-orange bg-colmena-orange"
                        : "border-gray-300"
                    }`}
                  />
                  <span className="text-sm font-bold text-gray-800">Personalizada</span>
                </div>
                <p className="text-xs text-gray-500 italic">Escribe tus propias etiquetas</p>
                <p className="text-[10px] text-gray-400 mt-1">Para instrumentos con escala propia</p>
              </button>
            </div>
          </div>

          {/* Número de puntos: solo los que realmente existen en el catálogo para este tipo */}
          {!isCustom && pointsForSelectedKind.length > 0 && (
            <div>
              <label className={LABEL_CLS}>Número de puntos</label>
              <div className="inline-flex rounded-lg border border-gray-200 overflow-hidden">
                {pointsForSelectedKind.map((pts) => (
                  <button
                    key={pts}
                    type="button"
                    onClick={() => applyPreset(selectedKey, pts)}
                    className={`px-5 py-2 text-sm font-semibold transition-colors ${
                      points === pts
                        ? "bg-colmena-orange text-white"
                        : "bg-white text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    {pts} puntos
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-gray-400 mt-2">
                5 puntos es el estándar en tesis. Un número impar deja un punto medio neutral.
              </p>
            </div>
          )}

          {/* Etiquetas editables */}
          <div>
            <label className={LABEL_CLS}>
              {isCustom ? "Puntos y etiquetas (agrega los que necesites)" : "Etiquetas (puedes afinarlas)"}
            </label>
            <div className="space-y-2">
              {scale.options.map((opt) => (
                <div key={opt.id} className="flex items-center gap-3">
                  {isCustom ? (
                    <input
                      className="w-12 h-10 rounded-lg border border-gray-200 bg-gray-50/30 text-center text-sm font-bold text-gray-700 outline-none transition focus:border-colmena-orange focus:ring-colmena-orange shrink-0"
                      type="number"
                      value={opt.value}
                      onChange={(e) => handleValueEdit(opt.id, Number(e.target.value))}
                    />
                  ) : (
                    <span className="w-8 h-8 rounded-lg bg-gray-100 text-gray-500 text-xs font-bold flex items-center justify-center shrink-0">
                      {opt.value}
                    </span>
                  )}
                  <input
                    className="flex-1 p-2.5 border border-gray-200 rounded-lg focus:ring-colmena-orange focus:border-colmena-orange bg-gray-50/30 outline-none transition text-sm"
                    type="text"
                    placeholder={isCustom ? `Etiqueta del punto ${opt.value}` : undefined}
                    value={opt.label}
                    onChange={(e) => handleLabelEdit(opt.id, e.target.value)}
                  />
                  {isCustom && scale.options.length > 2 && (
                    <button
                      type="button"
                      onClick={() => removeOption(opt.id)}
                      title="Quitar punto"
                      className="shrink-0 p-2 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            {isCustom && (
              <button
                type="button"
                onClick={addOption}
                className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-dashed border-gray-300 px-3 py-2 text-[12px] font-semibold text-gray-500 hover:border-colmena-orange/50 hover:text-colmena-orange transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Agregar punto
              </button>
            )}

            <p className="text-[10px] text-gray-400 mt-2">
              El número es el puntaje que se usará al sumar los ítems para el baremo.
            </p>
          </div>
        </div>

        {/* ── Columna derecha: vista previa en vivo ── */}
        <div className="col-span-5">
          <label className={LABEL_CLS}>Así lo verá el encuestado</label>
          <div className="sticky top-4 border border-gray-200 rounded-xl bg-white shadow-sm overflow-hidden">
            <div className="px-4 py-2 bg-gray-50 border-b border-gray-100 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-gray-300" />
              <span className="w-2 h-2 rounded-full bg-gray-300" />
              <span className="text-[10px] text-gray-400 ml-2">Vista previa del formulario</span>
            </div>
            <div className="p-5">
              <p className="text-sm font-semibold text-gray-800 mb-4">
                <span className="text-colmena-orange mr-1.5">1.</span>
                {previewText}
              </p>
              <div className="space-y-2.5">
                {scale.options.map((opt) => (
                  <label
                    key={opt.id}
                    className={`flex items-center gap-3 p-2.5 rounded-lg border cursor-pointer transition-colors ${
                      previewValue === opt.value
                        ? "border-colmena-orange bg-colmena-orange/5"
                        : "border-gray-100 hover:border-gray-200"
                    }`}
                  >
                    <input
                      type="radio"
                      name="scale-preview"
                      className="accent-colmena-orange w-4 h-4"
                      checked={previewValue === opt.value}
                      onChange={() => setPreviewValue(opt.value)}
                    />
                    <span className="text-sm text-gray-700">{opt.label || "…"}</span>
                  </label>
                ))}
              </div>
              {previewValue !== null && (
                <p className="text-[10px] text-gray-400 mt-3">
                  Esta respuesta aportaría <span className="font-bold text-gray-600">{previewValue}</span>{" "}
                  {previewValue === 1 ? "punto" : "puntos"} a la suma de su dimensión.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
