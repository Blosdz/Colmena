import { useState, useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Palette, LayoutTemplate, Save, CheckCircle2, Copy, Check } from "lucide-react";

import { getProject } from "../api/projects";
import { buildPublicFormUrl } from "../config/env";
import { listProjectForms, listQuestions, listQuestionOptions } from "../api/forms";
import type { FormQuestionOption } from "../types/form";
import type { PublicFormOptionRead, PublicFormQuestionRead } from "../types/publicForm";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { PageHeader } from "../components/layout/PageHeader";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";
import { apiClient } from "../api/client";
import {
  SurveyShell,
  SurveyProgressHeader,
  SurveyQuestionRenderer,
} from "../components/forms/survey/SurveyKit";
import {
  resolveSurveyTheme,
  getSurveySkin,
  SURVEY_SKINS,
  EDITABLE_SURVEY_COLORS,
  QUESTIONS_PER_SCREEN_OPTIONS,
  ALIGN_OPTIONS,
  type SurveyTheme,
} from "../design/surveyThemes";

const CHOICE_TYPES = ["likert", "single_choice", "multiple_choice", "dropdown", "boolean"];

/** Convierte un ítem del instrumento a la forma que espera SurveyQuestionRenderer. */
function toPreviewQuestion(
  id: string,
  label: string,
  type: string,
  options: PublicFormOptionRead[] | undefined,
): PublicFormQuestionRead {
  return {
    id,
    label,
    question_type: type,
    question_role: "item",
    measurement_level: "ordinal",
    data_type: "numeric",
    is_required: true,
    is_scored: false,
    is_reverse_scored: false,
    sort_order: 0,
    options: options ?? [],
  };
}

export function ProjectFormDesigner() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const [theme, setTheme] = useState<SurveyTheme>(() => resolveSurveyTheme(undefined));
  const [previewAnswers, setPreviewAnswers] = useState<Record<string, Record<string, unknown>>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [urlCopied, setUrlCopied] = useState(false);

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });

  const formsQuery = useQuery({
    queryKey: ["project-forms", projectId],
    queryFn: () => listProjectForms(projectId),
    enabled: Boolean(projectId),
  });

  const primaryForm = formsQuery.data?.items?.[0] || null;

  const questionsQuery = useQuery({
    queryKey: ["form-questions", primaryForm?.id],
    queryFn: () => listQuestions(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });

  const formQuestions = questionsQuery.data?.items || [];
  const validQuestions = formQuestions.filter(
    (q) => q.question_type !== "exogenous" && q.question_role !== "exogenous",
  );

  const previewChoiceIds = useMemo(
    () =>
      validQuestions
        .slice(0, 3)
        .filter((q) => CHOICE_TYPES.includes(q.question_type))
        .map((q) => q.id),
    [validQuestions],
  );

  const optionsQuery = useQuery({
    queryKey: ["preview-question-options", primaryForm?.id, previewChoiceIds],
    queryFn: async () => {
      const entries = await Promise.all(
        previewChoiceIds.map(async (id) => [id, (await listQuestionOptions(id)).items] as const),
      );
      return Object.fromEntries(entries) as Record<string, FormQuestionOption[]>;
    },
    enabled: previewChoiceIds.length > 0,
  });
  const optionsMap = optionsQuery.data || {};

  // Hydrate theme from metadata_json (soporta el formato viejo del diseñador).
  useEffect(() => {
    if (primaryForm?.metadata_json) {
      try {
        setTheme(resolveSurveyTheme(JSON.parse(primaryForm.metadata_json).theme));
      } catch (e) {
        console.error("Error parsing form metadata_json:", e);
      }
    }
  }, [primaryForm]);

  if (projectQuery.isLoading || formsQuery.isLoading) {
    return <LoadingState label="Cargando entorno de diseño..." />;
  }
  if (projectQuery.isError) {
    return <ErrorState message="Error al cargar el proyecto." />;
  }

  const skinDef = getSurveySkin(theme.skin);

  const setColor = (key: string, hex: string) =>
    setTheme((t) => ({ ...t, colors: { ...t.colors, [key]: hex } }));
  const selectSkin = (skinId: SurveyTheme["skin"]) =>
    setTheme((t) => ({ ...t, skin: skinId, colors: getSurveySkin(skinId).defaultColors }));

  const hasPublicUrl = Boolean(primaryForm?.public_slug);
  const publicFormUrl = hasPublicUrl
    ? buildPublicFormUrl(primaryForm!.public_slug!)
    : "Publica el formulario para generar el enlace público";

  const handleCopyUrl = async () => {
    if (!hasPublicUrl) return;
    try {
      if (navigator?.clipboard) await navigator.clipboard.writeText(publicFormUrl);
      setUrlCopied(true);
      setTimeout(() => setUrlCopied(false), 2000);
    } catch (err) {
      console.error("Error copying form URL:", err);
    }
  };

  const handleSave = async () => {
    if (!primaryForm) return;
    setIsSaving(true);
    try {
      // Conserva cualquier otra clave que ya viviera en metadata_json.
      let existing: Record<string, unknown> = {};
      try {
        existing = primaryForm.metadata_json ? JSON.parse(primaryForm.metadata_json) : {};
      } catch {
        existing = {};
      }
      await apiClient.patch(`/api/v1/forms/${primaryForm.id}`, {
        metadata_json: JSON.stringify({ ...existing, theme }),
      });
      setIsSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error("Error saving form design:", err);
      setIsSaving(false);
    }
  };

  const previewQuestions: PublicFormQuestionRead[] = validQuestions.slice(0, 4).map((q) => {
    const real = optionsMap[q.id];
    const isChoice = CHOICE_TYPES.includes(q.question_type);
    const opts: PublicFormOptionRead[] | undefined = real
      ? real.map((o, i) => ({ id: o.id, label: o.label, value: o.value, sort_order: i }))
      : isChoice
        ? [1, 2, 3, 4, 5].map((n) => ({ id: `${q.id}-${n}`, label: String(n), value: String(n), sort_order: n }))
        : undefined;
    return toPreviewQuestion(q.id, q.label, q.question_type, opts);
  });

  return (
    <div className="flex h-[calc(100vh-64px)] min-h-0 flex-col gap-5 overflow-hidden p-6 animate-colmena-fade-in">
      <PageHeader
        title="Diseño del Formulario"
        description="Elige cómo se ve la encuesta para quien la responde y ajusta sus colores."
        actions={
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="colmena-button-primary inline-flex items-center gap-2 px-5"
          >
            {isSaving ? (
              <div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            ) : saved ? (
              <CheckCircle2 className="w-4 h-4" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {isSaving ? "Guardando..." : saved ? "¡Guardado!" : "Guardar Diseño"}
          </button>
        }
      />

      <div className="flex flex-1 min-h-0 gap-6">
        {/* Sidebar */}
        <div className="w-[340px] shrink-0 flex flex-col gap-5 overflow-y-auto min-h-0 pr-2 pb-4">
          <section className="bg-white rounded-2xl border border-border p-5 shadow-sm space-y-5">
            <div className="flex items-center gap-2 text-dark font-semibold">
              <Palette className="w-5 h-5 text-amber" />
              <h3>Apariencia</h3>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase tracking-wider">Estilo</label>
              <div className="grid grid-cols-1 gap-2">
                {Object.values(SURVEY_SKINS).map((skin) => {
                  const active = theme.skin === skin.id;
                  return (
                    <button
                      key={skin.id}
                      type="button"
                      onClick={() => selectSkin(skin.id)}
                      className={`flex flex-col gap-2 rounded-xl border p-3 text-left transition-colors ${
                        active ? "border-amber bg-amber/5" : "border-border hover:border-amber/40"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-dark">{skin.label}</span>
                        {active && <Check className="w-4 h-4 text-amber" strokeWidth={3} />}
                      </div>
                      <p className="text-xs text-muted leading-4">{skin.description}</p>
                      <div className="flex items-center gap-1.5">
                        {Object.values(skin.defaultColors).map((hex) => (
                          <span key={hex} className="h-4 w-4 rounded-full border border-black/10" style={{ background: hex }} />
                        ))}
                        <span className="ml-1 text-[11px] text-muted">Tipografía {skin.fontLabel}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase tracking-wider">Colores</label>
              {EDITABLE_SURVEY_COLORS.map(({ key, label }) => (
                <label
                  key={key}
                  className="flex items-center justify-between gap-3 rounded-xl border border-border px-3 py-2"
                >
                  <span className="text-sm text-dark">{label}</span>
                  <input
                    type="color"
                    value={theme.colors[key]}
                    onChange={(e) => setColor(key, e.target.value)}
                    className="h-8 w-10 cursor-pointer rounded border border-border bg-transparent p-0"
                  />
                </label>
              ))}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase tracking-wider">Preguntas por pantalla</label>
              <div className="flex flex-wrap gap-1.5">
                {QUESTIONS_PER_SCREEN_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    title={opt.description}
                    onClick={() => setTheme((t) => ({ ...t, layout: { ...t.layout, questionsPerScreen: opt.id } }))}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      theme.layout.questionsPerScreen === opt.id
                        ? "border-amber bg-amber/5 text-amber"
                        : "border-border text-muted hover:bg-gray-50"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase tracking-wider">Alineación</label>
              <div className="flex gap-1.5">
                {ALIGN_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setTheme((t) => ({ ...t, layout: { ...t.layout, align: opt.id } }))}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      theme.layout.align === opt.id
                        ? "border-amber bg-amber/5 text-amber"
                        : "border-border text-muted hover:bg-gray-50"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          </section>
        </div>

        {/* Canvas / live preview */}
        <div className="flex-1 min-h-0 rounded-[24px] overflow-hidden border border-border shadow-inner relative flex flex-col">
          <div className="h-12 bg-white/80 backdrop-blur-md border-b border-border flex items-center px-4 shrink-0 z-10">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="w-3 h-3 rounded-full bg-amber-400" />
              <div className="w-3 h-3 rounded-full bg-green-400" />
            </div>
            <button
              type="button"
              onClick={handleCopyUrl}
              title="Copiar enlace del formulario público"
              className="group mx-auto flex items-center justify-center gap-2 bg-gray-100/80 hover:bg-amber/10 rounded-full h-7 max-w-[70%] px-4 text-[10px] font-mono transition-colors cursor-pointer"
            >
              <span className={`truncate ${urlCopied ? "text-green-600" : "text-muted group-hover:text-amber"}`}>
                {publicFormUrl}
              </span>
              {urlCopied ? (
                <Check className="w-3 h-3 shrink-0 text-green-600" />
              ) : (
                <Copy className="w-3 h-3 shrink-0 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </button>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto">
            <SurveyShell theme={theme} preview style={{ minHeight: "auto" }}>
              <SurveyProgressHeader
                studyName={primaryForm?.title || projectQuery.data?.title || "Formulario"}
                answered={Object.keys(previewAnswers).length}
                total={previewQuestions.length}
              />
              <main className="survey-main">
                <div className="survey-card">
                  <span className="survey-label" style={{ fontFamily: skinDef.fontLabel }}>
                    Vista previa · así lo verán tus participantes
                  </span>
                  {previewQuestions.length === 0 ? (
                    <div style={{ textAlign: "center", padding: "40px 0" }}>
                      <LayoutTemplate className="w-8 h-8 mx-auto mb-3" style={{ color: "var(--survey-muted)" }} />
                      <p className="survey-short-label">Este formulario aún no tiene ítems.</p>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-6" style={{ marginTop: 16 }}>
                      {previewQuestions.map((q, i) => (
                        <div key={q.id} className="flex flex-col gap-3">
                          <p className="survey-question-text" style={{ fontSize: 16 }}>
                            {i + 1}. {q.label}
                          </p>
                          <SurveyQuestionRenderer
                            question={q}
                            answer={
                              previewAnswers[q.id]
                                ? ({ question_id: q.id, ...previewAnswers[q.id] } as never)
                                : undefined
                            }
                            onChange={(patch) =>
                              setPreviewAnswers((prev) => ({ ...prev, [q.id]: { ...prev[q.id], ...patch } }))
                            }
                          />
                        </div>
                      ))}
                      {validQuestions.length > previewQuestions.length && (
                        <p className="survey-short-label" style={{ textAlign: "center", fontStyle: "italic" }}>
                          + {validQuestions.length - previewQuestions.length} ítems adicionales…
                        </p>
                      )}
                    </div>
                  )}
                </div>
                <div className="survey-footer">
                  <button type="button" className="survey-btn survey-btn-secondary" disabled>
                    Atrás
                  </button>
                  <button type="button" className="survey-btn survey-btn-primary survey-btn--wide" disabled>
                    Continuar
                  </button>
                </div>
              </main>
            </SurveyShell>
          </div>
        </div>
      </div>
    </div>
  );
}
