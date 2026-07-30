import { useState, useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Palette,
  LayoutTemplate,
  Plus,
  Save,
  CheckCircle2,
  Trash2,
  User,
  Briefcase,
  GraduationCap,
  Calendar,
  Image as ImageIcon,
  Copy,
  Check
} from "lucide-react";

import { getProject } from "../api/projects";
import { buildPublicFormUrl } from "../config/env";
import { listProjectForms, listQuestions, createQuestion, createQuestionOption, listQuestionOptions } from "../api/forms";
import type { FormQuestionOption } from "../types/form";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { PageHeader } from "../components/layout/PageHeader";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";
import { apiClient } from "../api/client";
import {
  ColmenaFormShell,
  ColmenaQuestionField,
  ColmenaLikertMatrix,
  groupQuestionsForMatrix,
  useResolvedFormTheme,
  DEFAULT_PRIMARY_COLOR,
  SYSTEM_BG,
  type FormTheme,
  type RenderField,
} from "../components/forms/FormSurface";

type ExogenousField = {
  id: string;
  label: string;
  type: "text" | "select" | "number" | "date";
  options?: string[];
};

const THEME_COLORS = [
  { name: "Amarillo", value: "#F5B21A" },
  { name: "Naranja", value: "#FF6A2A" },
  { name: "Turquesa", value: "#11B7B2" },
  { name: "Grafito", value: "#1C1F24" },
];

const PREDEFINED_FIELDS = [
  { icon: User, label: "Sexo", type: "select" as const, options: ["Masculino", "Femenino", "Prefiero no decirlo"] },
  { icon: Calendar, label: "Edad", type: "number" as const },
  { icon: Briefcase, label: "Ocupación / Cargo", type: "text" as const },
  { icon: GraduationCap, label: "Nivel de Estudios", type: "select" as const, options: ["Básico", "Medio", "Superior", "Posgrado"] },
];

export function ProjectFormDesigner() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const [theme, setTheme] = useState<FormTheme>({
    primaryColor: DEFAULT_PRIMARY_COLOR,
    backgroundColor: SYSTEM_BG,
    fontFamily: "Inter, sans-serif",
  });

  const [fields, setFields] = useState<ExogenousField[]>([]);
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

  // "system" background follows the OS light/dark preference for the preview.
  const resolvedTheme = useResolvedFormTheme(theme);

  // Ids of the choice-type items shown in the preview (first 3), so we can fetch
  // their real response-scale options (value + classification label).
  const previewChoiceIds = useMemo(() => {
    const items = questionsQuery.data?.items || [];
    return items
      .filter((q) => q.question_type !== "exogenous" && q.question_role !== "exogenous")
      .slice(0, 3)
      .filter((q) =>
        ["likert", "single_choice", "multiple_choice", "dropdown", "boolean"].includes(q.question_type)
      )
      .map((q) => q.id);
  }, [questionsQuery.data]);

  const optionsQuery = useQuery({
    queryKey: ["preview-question-options", primaryForm?.id, previewChoiceIds],
    queryFn: async () => {
      const entries = await Promise.all(
        previewChoiceIds.map(
          async (id) => [id, (await listQuestionOptions(id)).items] as const
        )
      );
      return Object.fromEntries(entries) as Record<string, FormQuestionOption[]>;
    },
    enabled: previewChoiceIds.length > 0,
  });
  const optionsMap = optionsQuery.data || {};

  // Hydrate designer settings from primaryForm.metadata_json
  useEffect(() => {
    if (primaryForm && primaryForm.metadata_json) {
      try {
        const meta = JSON.parse(primaryForm.metadata_json);
        if (meta.theme) {
          setTheme(meta.theme);
        }
        if (meta.exogenous_fields) {
          setFields(meta.exogenous_fields);
        }
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

  const addField = (fieldInfo: typeof PREDEFINED_FIELDS[0]) => {
    setFields((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        label: fieldInfo.label,
        type: fieldInfo.type,
        options: fieldInfo.options,
      },
    ]);
  };

  const removeField = (id: string) => {
    setFields((prev) => prev.filter((f) => f.id !== id));
  };

  // Enlace público real del formulario (accesible vía AppThesis como tenant).
  // Solo existe cuando el formulario está publicado (tiene public_slug).
  const hasPublicUrl = Boolean(primaryForm?.public_slug);
  const publicFormUrl = hasPublicUrl
    ? buildPublicFormUrl(primaryForm!.public_slug!)
    : "Publica el formulario para generar el enlace público";

  const handleCopyUrl = async () => {
    if (!hasPublicUrl) return;
    try {
      if (navigator?.clipboard) {
        await navigator.clipboard.writeText(publicFormUrl);
      }
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
      // 1. Save theme & fields in Form.metadata_json
      const metadata = {
        theme,
        exogenous_fields: fields,
      };
      await apiClient.patch(`/api/v1/forms/${primaryForm.id}`, {
        metadata_json: JSON.stringify(metadata),
      });

      // 2. Fetch current questions to clean up old exogenous questions
      const qResponse = await listQuestions(primaryForm.id);
      const oldExogenous = qResponse.items.filter(
        q => q.question_role === "exogenous" || q.question_type === "exogenous"
      );

      // Delete old ones
      for (const q of oldExogenous) {
        await apiClient.delete(`/api/v1/form-questions/${q.id}`);
      }

      // 3. Create new exogenous questions in form_questions table
      for (let idx = 0; idx < fields.length; idx++) {
        const field = fields[idx];
        const mappedType =
          field.type === "select"
            ? "dropdown"
            : field.type === "text"
            ? "text_short"
            : field.type; // number, date, etc.

        const question = await createQuestion(primaryForm.id, {
          label: field.label,
          question_type: mappedType,
          question_role: "exogenous",
          measurement_level: field.type === "select" ? "nominal" : "interval",
          data_type: field.type === "number" ? "numeric" : "text",
          is_required: true,
          is_scored: false,
          is_reverse_scored: false,
          sort_order: -100 + idx, // place them at the beginning of the form
          help_text: "Pregunta sociodemográfica exógena",
        });

        // If it has options, create option records
        if (field.options && field.options.length > 0) {
          for (let optIdx = 0; optIdx < field.options.length; optIdx++) {
            const opt = field.options[optIdx];
            await createQuestionOption(question.id, {
              label: opt,
              value: opt,
              score: 0.0,
              sort_order: optIdx,
            });
          }
        }
      }

      setIsSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error("Error saving form design:", err);
      setIsSaving(false);
    }
  };

  const formQuestions = questionsQuery.data?.items || [];
  const validQuestions = formQuestions.filter((q) => q.question_type !== "exogenous" && q.question_role !== "exogenous");

  return (
    <div className="flex h-full flex-col gap-6 p-6 animate-colmena-fade-in">
      <PageHeader
        title="Diseño del Formulario"
        description="Agrega variables sociodemográficas y personaliza la apariencia visual de tu instrumento."
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
        {/* Sidebar Tools */}
        <div className="w-[320px] shrink-0 flex flex-col gap-5 overflow-y-auto pr-2 pb-8">
          
          {/* Sociodemographics */}
          <section className="bg-white rounded-2xl border border-border p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-dark font-semibold">
              <User className="w-5 h-5 text-amber" />
              <h3>Variables Exógenas</h3>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Haz clic para añadir preguntas demográficas al inicio de tu formulario.
            </p>
            <div className="grid grid-cols-1 gap-2">
              {PREDEFINED_FIELDS.map((field) => (
                <button
                  key={field.label}
                  onClick={() => addField(field)}
                  className="flex items-center justify-between p-3 rounded-xl border border-border bg-[#FCFCFB] hover:border-amber/40 hover:bg-amber/5 transition-all group text-left"
                >
                  <div className="flex items-center gap-3">
                    <field.icon className="w-4 h-4 text-muted group-hover:text-amber" />
                    <span className="text-sm font-medium text-dark">{field.label}</span>
                  </div>
                  <Plus className="w-4 h-4 text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
              <button className="flex items-center justify-center gap-2 p-3 rounded-xl border border-dashed border-border text-sm font-medium text-muted hover:border-dark hover:text-dark transition-all mt-2">
                <Plus className="w-4 h-4" />
                Crear campo personalizado
              </button>
            </div>
          </section>

          {/* Theme Settings */}
          <section className="bg-white rounded-2xl border border-border p-5 shadow-sm space-y-5">
            <div className="flex items-center gap-2 text-dark font-semibold">
              <Palette className="w-5 h-5 text-amber" />
              <h3>Apariencia</h3>
            </div>
            
            <div className="space-y-3">
              <label className="text-xs font-semibold text-muted uppercase tracking-wider">Color Principal</label>
              <div className="flex flex-wrap items-center gap-3">
                {THEME_COLORS.map((color) => (
                  <button
                    key={color.name}
                    onClick={() => setTheme({ ...theme, primaryColor: color.value })}
                    className={`w-8 h-8 rounded-full border-2 transition-all ${
                      theme.primaryColor === color.value ? "border-dark scale-110 shadow-md" : "border-transparent"
                    }`}
                    style={{ backgroundColor: color.value }}
                    title={color.name}
                  />
                ))}
                <label
                  title="Color personalizado"
                  className="relative w-8 h-8 rounded-full border-2 border-dashed border-border flex items-center justify-center cursor-pointer hover:border-amber transition-all overflow-hidden"
                  style={
                    THEME_COLORS.every((c) => c.value !== theme.primaryColor)
                      ? { borderStyle: "solid", borderColor: "#111111", transform: "scale(1.1)", backgroundColor: theme.primaryColor }
                      : undefined
                  }
                >
                  {THEME_COLORS.every((c) => c.value !== theme.primaryColor) ? null : (
                    <Palette className="w-4 h-4 text-muted" />
                  )}
                  <input
                    type="color"
                    value={theme.primaryColor}
                    onChange={(e) => setTheme({ ...theme, primaryColor: e.target.value })}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                </label>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <label className="text-xs font-semibold text-muted uppercase tracking-wider">Fondo</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => setTheme({ ...theme, backgroundColor: SYSTEM_BG })}
                  className={`p-3 rounded-xl border text-sm font-medium transition-all ${
                    theme.backgroundColor === SYSTEM_BG ? "border-amber bg-amber/5 text-amber" : "border-border text-muted hover:bg-gray-50"
                  }`}
                >
                  Sistema
                </button>
                <button
                  onClick={() => setTheme({ ...theme, backgroundColor: "#F3F4F6" })}
                  className={`p-3 rounded-xl border text-sm font-medium transition-all ${
                    theme.backgroundColor === "#F3F4F6" ? "border-amber bg-amber/5 text-amber" : "border-border text-muted hover:bg-gray-50"
                  }`}
                >
                  Claro
                </button>
                <button
                  onClick={() => setTheme({ ...theme, backgroundColor: "#121212" })}
                  className={`p-3 rounded-xl border text-sm font-medium transition-all ${
                    theme.backgroundColor === "#121212" ? "border-amber bg-amber/5 text-amber" : "border-border text-muted hover:bg-gray-50"
                  }`}
                >
                  Oscuro
                </button>
              </div>
              <p className="text-[11px] text-muted leading-snug">
                «Sistema» sigue el modo claro/oscuro del dispositivo de cada participante.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <label className="text-xs font-semibold text-muted uppercase tracking-wider">Logotipo</label>
              <button className="w-full flex flex-col items-center justify-center gap-2 p-6 rounded-xl border border-dashed border-border text-muted hover:border-amber hover:text-amber transition-all bg-gray-50">
                <ImageIcon className="w-6 h-6" />
                <span className="text-xs font-medium">Subir imagen</span>
              </button>
            </div>
          </section>
        </div>

        {/* Canvas Area */}
        <div
          className="flex-1 rounded-[32px] overflow-hidden border border-border shadow-inner relative flex flex-col"
          style={{ backgroundColor: resolvedTheme.backgroundColor }}
        >
          {/* Browser Bar Mockup */}
          <div className="h-12 bg-white/80 backdrop-blur-md border-b border-border flex items-center px-4 shrink-0 shadow-sm z-10">
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
              <span
                className={`truncate transition-colors ${
                  urlCopied ? "text-green-600" : "text-muted group-hover:text-amber group-hover:animate-pulse"
                }`}
              >
                {publicFormUrl}
              </span>
              {urlCopied ? (
                <Check className="w-3 h-3 shrink-0 text-green-600" />
              ) : (
                <Copy className="w-3 h-3 shrink-0 text-muted opacity-0 group-hover:opacity-100 group-hover:text-amber transition-opacity" />
              )}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-8 flex justify-center">
            <div className="w-full max-w-xl my-auto">
              <ColmenaFormShell
                theme={resolvedTheme}
                stepCurrent={1}
                stepTotal={validQuestions.length > 0 && fields.length > 0 ? 2 : 1}
                title={primaryForm?.title || projectQuery.data?.title || "Formulario de Estudio"}
                subtitle={
                  primaryForm?.description ||
                  "Por favor, completa las siguientes preguntas con honestidad. Tus respuestas son anónimas."
                }
                canBack={false}
                nextLabel="Siguiente"
              >
                {fields.length === 0 && validQuestions.length === 0 && (
                  <div className="text-center py-10">
                    <LayoutTemplate className="w-8 h-8 mx-auto mb-3 opacity-40" style={{ color: theme.primaryColor }} />
                    <p className="text-sm font-medium" style={{ color: "#A7A7A7" }}>
                      Aún no hay campos ni ítems
                    </p>
                    <p className="text-xs mt-1" style={{ color: "#777" }}>
                      Añade variables exógenas o configura el instrumento en el Workspace.
                    </p>
                  </div>
                )}

                {/* Exogenous fields (with hover remove) */}
                {fields.map((field) => {
                  const rf: RenderField = {
                    id: field.id,
                    label: field.label,
                    required: true,
                    type:
                      field.type === "select"
                        ? "dropdown"
                        : field.type === "text"
                        ? "text_short"
                        : field.type,
                    options: field.options?.map((o) => ({ id: o, label: o })),
                  };
                  return (
                    <div key={field.id} className="relative group">
                      <ColmenaQuestionField theme={resolvedTheme} field={rf} disabled />
                      <button
                        onClick={() => removeField(field.id)}
                        title="Quitar campo"
                        className="absolute -top-1 right-0 p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}

                {/* Instrument items preview (first 3) — real scale options when available */}
                {groupQuestionsForMatrix(
                  validQuestions.slice(0, 3).map((q) => {
                    const realOptions = optionsMap[q.id];
                    const isChoice =
                      q.question_type === "likert" || q.question_type === "single_choice";
                    const rf: RenderField = {
                      id: q.id,
                      label: q.label,
                      helpText: q.help_text,
                      required: q.is_required,
                      type: q.question_type,
                      dimensionId: q.dimension_id,
                      options: realOptions
                        ? realOptions.map((o) => ({ id: o.id, label: o.label, value: o.value }))
                        : isChoice
                        ? // Fallback while the scale loads / if none defined yet.
                          [1, 2, 3, 4, 5].map((n) => ({ id: `${q.id}-${n}`, label: String(n) }))
                        : undefined,
                    };
                    return rf;
                  })
                ).map((block, blockIdx) =>
                  block.kind === "matrix" ? (
                    <ColmenaLikertMatrix
                      key={`matrix-${blockIdx}`}
                      theme={resolvedTheme}
                      fields={block.fields}
                      scaleOptions={block.scaleOptions}
                      answers={{}}
                      disabled
                    />
                  ) : (
                    <ColmenaQuestionField
                      key={block.field.id}
                      theme={resolvedTheme}
                      field={block.field}
                      disabled
                    />
                  )
                )}

                {validQuestions.length > 3 && (
                  <p className="text-center text-xs italic" style={{ color: "#777" }}>
                    + {validQuestions.length - 3} ítems adicionales…
                  </p>
                )}
              </ColmenaFormShell>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
