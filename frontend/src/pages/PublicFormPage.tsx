import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Check, Clock, Info } from "lucide-react";

import { getPublicForm, submitPublicResponse } from "../api/publicForms";
import type { PublicAnswerCreate, PublicFormQuestionRead } from "../types/publicForm";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";
import { resolveSurveyTheme } from "../design/surveyThemes";
import {
  SurveyShell,
  SurveyProgressHeader,
  SurveyQuestionRenderer,
  SurveyAllQuestionsView,
  hasAnswer,
} from "../components/forms/survey/SurveyKit";

type Section = {
  id: string;
  title: string | null;
  description?: string | null;
  questions: PublicFormQuestionRead[];
};

function buildSections(form: {
  sections: { id: string; title: string; description?: string | null }[];
  questions: PublicFormQuestionRead[];
}): Section[] {
  const { sections, questions } = form;
  if (sections.length === 0) {
    return [{ id: "all", title: null, description: null, questions }];
  }
  const map: Record<string, PublicFormQuestionRead[]> = {};
  sections.forEach((s) => (map[s.id] = []));
  const loose: PublicFormQuestionRead[] = [];
  questions.forEach((q) => {
    if (q.section_id && map[q.section_id]) map[q.section_id].push(q);
    else loose.push(q);
  });
  const out: Section[] = sections
    .map((s) => ({ id: s.id, title: s.title, description: s.description, questions: map[s.id] || [] }))
    .filter((s) => s.questions.length > 0);
  if (loose.length > 0) {
    out.push({ id: "loose", title: "Preguntas generales", description: null, questions: loose });
  }
  return out;
}

export function PublicFormPage() {
  const { publicSlug = "" } = useParams();

  const [step, setStep] = useState<"welcome" | "questions" | "completed">("welcome");
  const [sectionIndex, setSectionIndex] = useState(0);
  const [respondentCode, setRespondentCode] = useState("");
  const [answers, setAnswers] = useState<Record<string, PublicAnswerCreate>>({});
  const [error, setError] = useState<string | null>(null);

  const { data: form, isLoading, error: loadError } = useQuery({
    queryKey: ["public-form", publicSlug],
    queryFn: () => getPublicForm(publicSlug),
    enabled: Boolean(publicSlug),
  });

  const theme = useMemo(() => {
    if (!form?.metadata_json) return resolveSurveyTheme(undefined);
    try {
      return resolveSurveyTheme(JSON.parse(form.metadata_json).theme);
    } catch {
      return resolveSurveyTheme(undefined);
    }
  }, [form?.metadata_json]);

  const sections = useMemo<Section[]>(() => (form ? buildSections(form) : []), [form]);
  const allQuestions = useMemo(() => sections.flatMap((s) => s.questions), [sections]);

  const submitMutation = useMutation({
    mutationFn: () =>
      submitPublicResponse(publicSlug, {
        respondent_code: respondentCode || undefined,
        answers: Object.values(answers),
        metadata_json: {
          user_agent: navigator.userAgent,
          submitted_at_local: new Date().toISOString(),
        },
      }),
    onSuccess: () => setStep("completed"),
    onError: (err: unknown) =>
      setError(
        err instanceof Error ? err.message : "No se pudieron enviar las respuestas. Revisa e intenta de nuevo.",
      ),
  });

  const setAnswer = (questionId: string, patch: Partial<PublicAnswerCreate>) => {
    setError(null);
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], question_id: questionId, ...patch },
    }));
  };

  const missingIn = (qs: PublicFormQuestionRead[]) =>
    qs.filter((q) => q.is_required && !hasAnswer(q, answers[q.id]));

  if (isLoading) {
    return (
      <SurveyShell theme={theme} style={{ display: "grid", placeItems: "center" }}>
        <LoadingState label="Cargando formulario…" />
      </SurveyShell>
    );
  }

  if (loadError || !form) {
    return (
      <SurveyShell theme={theme}>
        <main className="survey-main">
          <div className="survey-card">
            <p className="survey-label">Formulario no disponible</p>
            <p className="survey-question-text" style={{ marginTop: 8 }}>
              El enlace es inválido, expiró o el formulario fue cerrado.
            </p>
            <div style={{ marginTop: 16 }}>
              <ErrorState message={(loadError as Error)?.message || "Formulario no encontrado"} />
            </div>
          </div>
        </main>
      </SurveyShell>
    );
  }

  const answeredCount = allQuestions.filter((q) => hasAnswer(q, answers[q.id])).length;

  /* ── Welcome ── */
  if (step === "welcome") {
    return (
      <SurveyShell theme={theme}>
        <main className="survey-main">
          <div className="survey-card">
            <span className="survey-label">Estudio científico</span>
            <h1 className="survey-question-text" style={{ marginTop: 8, fontSize: 24 }}>
              {form.title}
            </h1>
            {form.description ? (
              <p className="survey-short-label" style={{ marginTop: 12, fontSize: 14 }}>
                {form.description}
              </p>
            ) : null}

            {form.instructions ? (
              <div className="survey-section-banner" style={{ marginTop: 20 }}>
                <p className="survey-section-title" style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <Info className="w-4 h-4" /> Instrucciones
                </p>
                <p className="survey-section-description" style={{ whiteSpace: "pre-wrap" }}>
                  {form.instructions}
                </p>
              </div>
            ) : null}

            <div className="survey-grid" style={{ marginTop: 20 }}>
              <div>
                <p className="survey-label">Preguntas</p>
                <p className="survey-question-text" style={{ fontSize: 18 }}>
                  {allQuestions.length}
                </p>
              </div>
              <div>
                <p className="survey-label">Tiempo estimado</p>
                <p className="survey-question-text" style={{ fontSize: 18, display: "flex", alignItems: "center", gap: 6 }}>
                  <Clock className="w-4 h-4" />~{Math.max(1, Math.round(allQuestions.length * 0.4))} min
                </p>
              </div>
            </div>

            <div style={{ marginTop: 20 }}>
              <label className="survey-label" htmlFor="respondent-code">
                Código de participante (opcional)
              </label>
              <input
                id="respondent-code"
                type="text"
                className="survey-input"
                style={{ marginTop: 6 }}
                placeholder="Déjalo vacío para responder de forma anónima"
                value={respondentCode}
                onChange={(e) => setRespondentCode(e.target.value)}
              />
            </div>
          </div>
          <div className="survey-footer" style={{ justifyContent: "flex-end" }}>
            <button
              type="button"
              className="survey-btn survey-btn-primary survey-btn--wide"
              onClick={() => setStep("questions")}
            >
              Comenzar
            </button>
          </div>
        </main>
      </SurveyShell>
    );
  }

  /* ── Completed ── */
  if (step === "completed") {
    return (
      <SurveyShell theme={theme}>
        <main className="survey-main">
          <div className="survey-card" style={{ textAlign: "center" }}>
            <div
              aria-hidden="true"
              style={{
                width: 72,
                height: 72,
                borderRadius: "50%",
                margin: "0 auto 20px",
                display: "grid",
                placeItems: "center",
                background: "var(--survey-accent)",
                color: "var(--survey-accent-text)",
              }}
            >
              <Check className="w-8 h-8" strokeWidth={3} />
            </div>
            <h1 className="survey-question-text">¡Respuestas registradas!</h1>
            <p className="survey-short-label" style={{ marginTop: 12, fontSize: 14 }}>
              {form.thank_you_message ||
                "Gracias por tu colaboración. Tu respuesta se guardó en la base de datos del estudio."}
            </p>
          </div>
        </main>
      </SurveyShell>
    );
  }

  /* ── Questions: "all" layout ── */
  if (theme.layout.questionsPerScreen === "all") {
    return (
      <SurveyShell theme={theme}>
        <SurveyProgressHeader studyName={form.title} answered={answeredCount} total={allQuestions.length} />
        <SurveyAllQuestionsView
          kicker="Estudio científico"
          title={form.title}
          description={form.description}
          sections={sections}
          answers={answers}
          onAnswerChange={setAnswer}
          submitting={submitMutation.isPending}
          error={error}
          onSubmit={() => {
            const missing = missingIn(allQuestions);
            if (missing.length > 0) {
              setError("Responde todas las preguntas obligatorias antes de enviar.");
              return;
            }
            submitMutation.mutate();
          }}
        />
      </SurveyShell>
    );
  }

  /* ── Questions: "single" layout (one section per screen) ── */
  const section = sections[sectionIndex];
  const isLast = sectionIndex === sections.length - 1;

  const goNext = () => {
    const missing = missingIn(section.questions);
    if (missing.length > 0) {
      setError("Responde todas las preguntas obligatorias antes de continuar.");
      return;
    }
    setError(null);
    if (isLast) submitMutation.mutate();
    else {
      setSectionIndex((i) => i + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };
  const goPrev = () => {
    setError(null);
    if (sectionIndex === 0) setStep("welcome");
    else {
      setSectionIndex((i) => i - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <SurveyShell theme={theme}>
      <SurveyProgressHeader studyName={form.title} answered={answeredCount} total={allQuestions.length} />
      <main className="survey-main">
        <div className="survey-card">
          <div className="survey-grid">
            <div>
              <p className="survey-label">
                Sección {sectionIndex + 1} de {sections.length}
              </p>
              {section.title ? <p className="survey-short-label">{section.title}</p> : null}
            </div>
            <div className="flex flex-col gap-6">
              {section.description ? (
                <p className="survey-short-label">{section.description}</p>
              ) : null}
              {section.questions.map((question) => {
                const answer = answers[question.id];
                const isMissing = error !== null && question.is_required && !hasAnswer(question, answer);
                return (
                  <div key={question.id} className="flex flex-col gap-3">
                    <p className="survey-question-text" style={{ fontSize: 16 }}>
                      {question.label}
                      {question.is_required ? " *" : ""}
                    </p>
                    {question.help_text ? (
                      <p className="survey-short-label">{question.help_text}</p>
                    ) : null}
                    <SurveyQuestionRenderer
                      question={question}
                      answer={answer}
                      onChange={(patch) => setAnswer(question.id, patch)}
                    />
                    {isMissing ? (
                      <p className="survey-required-note">Esta pregunta es obligatoria.</p>
                    ) : null}
                  </div>
                );
              })}
              {error ? <p className="survey-error-note">{error}</p> : null}
            </div>
          </div>
        </div>
        <div className="survey-footer">
          <button type="button" className="survey-btn survey-btn-secondary" onClick={goPrev}>
            Atrás
          </button>
          <button
            type="button"
            className="survey-btn survey-btn-primary survey-btn--wide"
            onClick={goNext}
            disabled={submitMutation.isPending}
          >
            {submitMutation.isPending ? "Enviando…" : isLast ? "Finalizar" : "Continuar"}
          </button>
        </div>
      </main>
    </SurveyShell>
  );
}

export default PublicFormPage;
