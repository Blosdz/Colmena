import { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Check, ChevronRight, Clock, Info, AlertTriangle } from "lucide-react";

import { getPublicForm, submitPublicResponse } from "../api/publicForms";
import type { PublicAnswerCreate, PublicFormQuestionRead } from "../types/publicForm";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";
import {
  ColmenaFormShell,
  ColmenaQuestionField,
  ColmenaLikertMatrix,
  ColmenaGradientHeader,
  groupQuestionsForMatrix,
  resolveFormPalette,
  useResolvedFormTheme,
  DEFAULT_FORM_THEME,
  type FormTheme,
  type RenderField,
} from "../components/forms/FormSurface";

const toRenderField = (q: PublicFormQuestionRead): RenderField => ({
  id: q.id,
  label: q.label,
  helpText: q.help_text,
  type: q.question_type,
  required: q.is_required,
  code: q.code,
  options: q.options?.map((o) => ({ id: o.id, label: o.label, value: o.value })),
  minValue: q.min_value,
  maxValue: q.max_value,
  dimensionId: q.dimension_id,
});

export function PublicFormPage() {
  const { publicSlug = "" } = useParams();

  const [step, setStep] = useState<"welcome" | "questions" | "completed">("welcome");
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [respondentCode, setRespondentCode] = useState("");
  const [answers, setAnswers] = useState<Record<string, PublicAnswerCreate>>({});
  const [validationError, setValidationError] = useState<string | null>(null);

  const transmissionId = useMemo(() => Math.random().toString(36).substring(2, 10).toUpperCase(), []);

  const { data: form, isLoading, error } = useQuery({
    queryKey: ["public-form", publicSlug],
    queryFn: () => getPublicForm(publicSlug),
    enabled: Boolean(publicSlug),
  });

  // Resolve theme (primary color / background / font) from the form metadata.
  const rawTheme = useMemo<FormTheme>(() => {
    if (!form?.metadata_json) return DEFAULT_FORM_THEME;
    try {
      const meta = JSON.parse(form.metadata_json);
      return { ...DEFAULT_FORM_THEME, ...(meta.theme || {}) };
    } catch {
      return DEFAULT_FORM_THEME;
    }
  }, [form?.metadata_json]);
  // "system" background follows the OS light/dark preference.
  const theme = useResolvedFormTheme(rawTheme);
  const p = resolveFormPalette(theme);

  const submitMutation = useMutation({
    mutationFn: (payload: { respondent_code: string; answers: PublicAnswerCreate[] }) =>
      submitPublicResponse(publicSlug, {
        respondent_code: payload.respondent_code || undefined,
        answers: payload.answers,
        metadata_json: {
          user_agent: navigator.userAgent,
          screen_size: `${window.innerWidth}x${window.innerHeight}`,
          submitted_at_local: new Date().toISOString(),
        },
      }),
    onSuccess: () => setStep("completed"),
    onError: (err: any) => {
      setValidationError(
        err.response?.data?.detail ||
          "Error al enviar las respuestas. Por favor, revisa tus respuestas e intenta de nuevo."
      );
    },
  });

  const pageWrap = (children: React.ReactNode) => (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6"
      style={{ background: p.pageBg, fontFamily: p.fontFamily }}
    >
      {children}
    </div>
  );

  if (isLoading) {
    return pageWrap(<LoadingState label="Cargando formulario…" />);
  }

  if (error || !form) {
    return pageWrap(
      <div
        className="max-w-md w-full rounded-[28px] p-8 text-center"
        style={{ background: p.cardBg, border: `1px solid ${p.cardBorder}` }}
      >
        <AlertTriangle className="w-14 h-14 mx-auto mb-4" style={{ color: "#EF4444" }} />
        <h2 className="text-2xl font-bold mb-2" style={{ color: p.title }}>
          Formulario no disponible
        </h2>
        <p className="text-sm mb-6" style={{ color: p.muted }}>
          El enlace de este formulario es inválido, ha expirado o el formulario ha sido cerrado por el
          investigador.
        </p>
        <ErrorState message={(error as Error)?.message || "Formulario no encontrado"} />
      </div>
    );
  }

  const { questions = [], sections = [], title, description, instructions, thank_you_message } = form;

  const getSectionsWithQuestions = () => {
    if (sections.length === 0) {
      return [
        {
          id: "default",
          title: "Cuestionario",
          description: "Por favor contesta todas las preguntas a continuación.",
          questions,
        },
      ];
    }

    const map: Record<string, typeof questions> = {};
    const unsectioned: typeof questions = [];
    sections.forEach((s) => {
      map[s.id] = [];
    });
    questions.forEach((q) => {
      if (q.section_id && map[q.section_id]) map[q.section_id].push(q);
      else unsectioned.push(q);
    });

    const activeSections = sections
      .map((s) => ({ id: s.id, title: s.title, description: s.description, questions: map[s.id] || [] }))
      .filter((s) => s.questions.length > 0);

    if (unsectioned.length > 0) {
      activeSections.push({
        id: "unsectioned",
        title: "Preguntas generales",
        description: "Preguntas del cuestionario",
        questions: unsectioned,
      });
    }
    return activeSections;
  };

  const formSections = getSectionsWithQuestions();
  const currentSection = formSections[currentSectionIndex] || null;

  const handleAnswerChange = (questionId: string, answer: Partial<PublicAnswerCreate>) => {
    setValidationError(null);
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], question_id: questionId, ...answer },
    }));
  };

  const validateCurrentSection = () => {
    if (!currentSection) return true;
    for (const q of currentSection.questions) {
      if (!q.is_required) continue;
      const ans = answers[q.id];
      if (!ans) return false;
      if (q.question_type === "text_short" || q.question_type === "text_long") {
        if (!ans.value_text || ans.value_text.trim() === "") return false;
      } else if (q.question_type === "number") {
        if (ans.value_number === undefined || ans.value_number === null) return false;
        if (q.min_value != null && ans.value_number < q.min_value) return false;
        if (q.max_value != null && ans.value_number > q.max_value) return false;
      } else if (q.question_type === "date") {
        if (!ans.value_date) return false;
      } else if (q.question_type === "multiple_choice") {
        if (!ans.value_json || !Array.isArray(ans.value_json) || ans.value_json.length === 0) return false;
      } else {
        if (!ans.option_id) return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (!validateCurrentSection()) {
      setValidationError("Por favor, responde todas las preguntas obligatorias antes de continuar.");
      return;
    }
    setValidationError(null);
    if (currentSectionIndex < formSections.length - 1) {
      setCurrentSectionIndex((prev) => prev + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      submitMutation.mutate({ respondent_code: respondentCode, answers: Object.values(answers) });
    }
  };

  const handlePrev = () => {
    setValidationError(null);
    if (currentSectionIndex > 0) {
      setCurrentSectionIndex((prev) => prev - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      setStep("welcome");
    }
  };

  const totalQuestions = questions.length;

  // ── WELCOME ────────────────────────────────────────────────────────────────
  if (step === "welcome") {
    return pageWrap(
      <div
        className="w-full max-w-xl rounded-[28px] overflow-hidden shadow-2xl"
        style={{ background: p.cardBg, border: `1px solid ${p.cardBorder}` }}
      >
        <ColmenaGradientHeader theme={theme} eyebrow="Estudio científico activo" title={title} />
        <div className="px-7 sm:px-10 pt-7 pb-9">
          {description && (
            <p className="text-sm sm:text-base leading-relaxed" style={{ color: p.text }}>
              {description}
            </p>
          )}

          {instructions && (
            <div
              className="mt-6 p-4 rounded-2xl"
              style={{ background: p.isLight ? "#F8FAFC" : "rgba(255,255,255,0.03)", border: `1px solid ${p.cardBorder}` }}
            >
              <h4 className="text-xs font-bold uppercase tracking-widest flex items-center gap-2 mb-1.5" style={{ color: p.muted }}>
                <Info className="w-3.5 h-3.5" style={{ color: p.primary }} />
                Instrucciones
              </h4>
              <p className="text-xs leading-relaxed whitespace-pre-wrap" style={{ color: p.text }}>
                {instructions}
              </p>
            </div>
          )}

          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            <div className="p-4 rounded-2xl" style={{ background: p.isLight ? "#F8FAFC" : "rgba(255,255,255,0.03)", border: `1px solid ${p.cardBorder}` }}>
              <span className="text-[10px] uppercase tracking-wider block" style={{ color: p.muted }}>
                Preguntas totales
              </span>
              <span className="text-lg font-bold" style={{ color: p.title }}>
                {totalQuestions} ítems
              </span>
            </div>
            <div className="p-4 rounded-2xl" style={{ background: p.isLight ? "#F8FAFC" : "rgba(255,255,255,0.03)", border: `1px solid ${p.cardBorder}` }}>
              <span className="text-[10px] uppercase tracking-wider block" style={{ color: p.muted }}>
                Tiempo estimado
              </span>
              <span className="text-lg font-bold flex items-center gap-1.5" style={{ color: p.title }}>
                <Clock className="w-4 h-4" style={{ color: p.primary }} />~
                {Math.max(1, Math.round(totalQuestions * 0.4))} min
              </span>
            </div>
          </div>

          <div className="mt-8 space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest" style={{ color: p.muted }}>
              Código de participante (opcional)
            </label>
            <input
              type="text"
              placeholder="Escribe tu código o déjalo vacío para anónimo"
              className="w-full h-12 px-4 rounded-md outline-none text-sm transition-colors"
              style={{ background: p.inputBg, border: `1px solid ${p.inputBorder}`, color: p.inputText }}
              value={respondentCode}
              onChange={(e) => setRespondentCode(e.target.value)}
              onFocus={(e) => (e.currentTarget.style.borderColor = p.primary)}
              onBlur={(e) => (e.currentTarget.style.borderColor = p.inputBorder)}
            />
          </div>

          <button
            onClick={() => setStep("questions")}
            className="mt-8 w-full rounded-full font-bold text-base flex items-center justify-center gap-2 transition-transform duration-150 hover:scale-[1.015] active:scale-[0.99]"
            style={{ background: p.primary, color: p.onPrimary, height: 52 }}
          >
            Comenzar
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  }

  // ── COMPLETED ───────────────────────────────────────────────────────────────
  if (step === "completed") {
    return pageWrap(
      <div
        className="max-w-md w-full rounded-[28px] p-8 text-center shadow-2xl"
        style={{ background: p.cardBg, border: `1px solid ${p.cardBorder}` }}
      >
        <div
          className="w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center"
          style={{ background: p.gradient }}
        >
          <Check className="w-9 h-9" strokeWidth={3} style={{ color: p.onPrimary }} />
        </div>
        <h2 className="text-3xl font-extrabold mb-3" style={{ color: p.title }}>
          ¡Respuestas registradas!
        </h2>
        <p className="text-sm leading-relaxed mb-8" style={{ color: p.text }}>
          {thank_you_message ||
            "Muchas gracias por tu colaboración. Tu respuesta ha sido integrada a la base de datos del estudio con éxito."}
        </p>
        <div
          className="rounded-2xl px-5 py-4 inline-flex flex-col gap-1 items-center justify-center w-full"
          style={{ background: p.isLight ? "#F8FAFC" : "rgba(255,255,255,0.03)", border: `1px solid ${p.cardBorder}` }}
        >
          <span className="text-[10px] uppercase tracking-widest" style={{ color: p.muted }}>
            Estado de transmisión
          </span>
          <span className="text-xs font-bold flex items-center gap-1.5" style={{ color: p.primary }}>
            <span className="w-2 h-2 rounded-full animate-ping" style={{ background: p.primary }} />
            Conexión segura y sincronizada
          </span>
        </div>
        <p className="mt-6 text-[10px]" style={{ color: p.muted }}>
          ID de transmisión: {transmissionId}
        </p>
      </div>
    );
  }

  // ── QUESTIONS (step-based, tarjeta COLMENA) ──────────────────────────────────
  return pageWrap(
    currentSection ? (
      <ColmenaFormShell
        theme={theme}
        stepCurrent={currentSectionIndex + 1}
        stepTotal={formSections.length}
        stepLabels={formSections.map((s) => s.title)}
        title={currentSection.title}
        subtitle={currentSection.description}
        onBack={handlePrev}
        onNext={handleNext}
        canBack
        nextLabel={currentSectionIndex === formSections.length - 1 ? "Finalizar" : "Siguiente"}
        nextDisabled={submitMutation.isPending}
        nextLoading={submitMutation.isPending}
        error={validationError}
      >
        {groupQuestionsForMatrix(currentSection.questions.map(toRenderField)).map((block, blockIdx) =>
          block.kind === "matrix" ? (
            <ColmenaLikertMatrix
              key={`matrix-${blockIdx}`}
              theme={theme}
              fields={block.fields}
              scaleOptions={block.scaleOptions}
              answers={answers}
              onChange={handleAnswerChange}
            />
          ) : (
            <ColmenaQuestionField
              key={block.field.id}
              theme={theme}
              field={block.field}
              answer={answers[block.field.id]}
              onChange={(partial) => handleAnswerChange(block.field.id, partial)}
            />
          )
        )}
      </ColmenaFormShell>
    ) : (
      <div style={{ color: p.muted }}>Este formulario no tiene preguntas.</div>
    )
  );
}
