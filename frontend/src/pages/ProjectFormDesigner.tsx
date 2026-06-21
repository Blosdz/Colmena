import { useState, useEffect } from "react";
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
  Image as ImageIcon
} from "lucide-react";

import { getProject } from "../api/projects";
import { listProjectForms, listQuestions, createQuestion, createQuestionOption } from "../api/forms";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { PageHeader } from "../components/layout/PageHeader";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";
import { apiClient } from "../api/client";

type FormTheme = {
  primaryColor: string;
  backgroundColor: string;
  fontFamily: string;
};

type ExogenousField = {
  id: string;
  label: string;
  type: "text" | "select" | "number" | "date";
  options?: string[];
};

const THEME_COLORS = [
  { name: "Amber", value: "#F5B21A" },
  { name: "Ocean", value: "#0EA5E9" },
  { name: "Emerald", value: "#10B981" },
  { name: "Purple", value: "#8B5CF6" },
  { name: "Rose", value: "#F43F5E" },
  { name: "Slate", value: "#64748B" },
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
    primaryColor: "#F5B21A",
    backgroundColor: "#F3F4F6",
    fontFamily: "Inter, sans-serif",
  });

  const [fields, setFields] = useState<ExogenousField[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

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
    <div className="flex h-full flex-col animate-colmena-fade-in">
      <div className="flex items-center justify-between pb-4">
        <PageHeader
          title="Diseño del Formulario"
          description="Agrega variables sociodemográficas y personaliza la apariencia visual de tu instrumento."
        />
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
      </div>

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
              <div className="flex flex-wrap gap-3">
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
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <label className="text-xs font-semibold text-muted uppercase tracking-wider">Fondo</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setTheme({ ...theme, backgroundColor: "#F3F4F6" })}
                  className={`p-3 rounded-xl border text-sm font-medium transition-all ${
                    theme.backgroundColor === "#F3F4F6" ? "border-amber bg-amber/5 text-amber" : "border-border text-muted hover:bg-gray-50"
                  }`}
                >
                  Claro
                </button>
                <button
                  onClick={() => setTheme({ ...theme, backgroundColor: "#1F2937" })}
                  className={`p-3 rounded-xl border text-sm font-medium transition-all ${
                    theme.backgroundColor === "#1F2937" ? "border-amber bg-amber/5 text-amber" : "border-border text-muted hover:bg-gray-50"
                  }`}
                >
                  Oscuro
                </button>
              </div>
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
          style={{ backgroundColor: theme.backgroundColor }}
        >
          {/* Browser Bar Mockup */}
          <div className="h-12 bg-white/80 backdrop-blur-md border-b border-border flex items-center px-4 shrink-0 shadow-sm z-10">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="w-3 h-3 rounded-full bg-amber-400" />
              <div className="w-3 h-3 rounded-full bg-green-400" />
            </div>
            <div className="mx-auto bg-gray-100/80 rounded-full h-7 w-1/2 flex items-center justify-center text-[10px] text-muted font-mono">
              colmena.app/f/{primaryForm?.id?.slice(0, 8) || "demo"}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-8 flex justify-center">
            <div 
              className="w-full max-w-2xl bg-white rounded-2xl shadow-lg overflow-hidden my-auto"
              style={{ fontFamily: theme.fontFamily }}
            >
              {/* Form Header */}
              <div 
                className="h-3 w-full" 
                style={{ backgroundColor: theme.primaryColor }} 
              />
              <div className="px-10 pt-12 pb-8 border-b border-gray-100 space-y-3">
                <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
                  {primaryForm?.title || projectQuery.data?.title || "Formulario de Estudio"}
                </h1>
                <p className="text-gray-500 leading-relaxed text-sm">
                  {primaryForm?.description || "Por favor, completa las siguientes preguntas con honestidad. Tus respuestas son anónimas."}
                </p>
              </div>

              <div className="px-10 py-8 space-y-8 bg-gray-50/50">
                {/* Exogenous Fields Preview */}
                {fields.length > 0 && (
                  <div className="space-y-6">
                    <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-6">
                      Datos Sociodemográficos
                    </h2>
                    {fields.map((field) => (
                      <div key={field.id} className="space-y-2 group relative">
                        <label className="block text-sm font-semibold text-gray-700">
                          {field.label}
                        </label>
                        {field.type === "text" && (
                          <input disabled className="w-full h-11 px-4 rounded-xl border border-gray-200 bg-white shadow-sm" placeholder="Tu respuesta..." />
                        )}
                        {field.type === "number" && (
                          <input disabled className="w-32 h-11 px-4 rounded-xl border border-gray-200 bg-white shadow-sm" placeholder="Ej: 25" />
                        )}
                        {field.type === "select" && (
                          <div className="w-full h-11 px-4 rounded-xl border border-gray-200 bg-white shadow-sm flex items-center justify-between text-gray-400">
                            <span>Selecciona una opción...</span>
                            <div className="w-4 h-4" />
                          </div>
                        )}
                        
                        {/* Remove button (shows on hover) */}
                        <button 
                          onClick={() => removeField(field.id)}
                          className="absolute -right-12 top-6 p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    
                    <div className="h-px w-full bg-gray-200 my-8" />
                  </div>
                )}

                {/* Psychometric Items Preview */}
                <div>
                  <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-6">
                    Instrumento Principal
                  </h2>
                  
                  {validQuestions.length > 0 ? (
                    <div className="space-y-6">
                      {validQuestions.slice(0, 3).map((q, i) => (
                        <div key={q.id} className="space-y-3">
                          <p className="text-sm font-medium text-gray-800 leading-relaxed">
                            <span className="text-gray-400 mr-2">{i + 1}.</span>
                            {q.label}
                          </p>
                          <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((opt) => (
                              <div key={opt} className="w-8 h-8 rounded-full border border-gray-200 bg-white flex items-center justify-center text-xs text-gray-400">
                                {opt}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                      {validQuestions.length > 3 && (
                        <div className="pt-4 flex items-center justify-center text-sm text-gray-400 italic">
                          + {validQuestions.length - 3} ítems adicionales...
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-2xl">
                      <LayoutTemplate className="w-8 h-8 text-gray-300 mx-auto mb-3" />
                      <p className="text-sm text-gray-500 font-medium">No hay ítems cargados</p>
                      <p className="text-xs text-gray-400 mt-1">Configura el instrumento en el Workspace primero.</p>
                    </div>
                  )}
                </div>
                
                {/* Submit button preview */}
                <div className="pt-6">
                  <button 
                    disabled 
                    className="h-12 px-8 rounded-xl text-white font-semibold shadow-md transition-all w-full md:w-auto"
                    style={{ backgroundColor: theme.primaryColor }}
                  >
                    Enviar Respuestas
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
