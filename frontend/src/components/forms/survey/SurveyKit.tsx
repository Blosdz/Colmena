import type { CSSProperties, PropsWithChildren } from "react";

import type { PublicAnswerCreate, PublicFormQuestionRead } from "../../../types/publicForm";
import {
  buildSurveyThemeVars,
  type SurveyTheme,
} from "../../../design/surveyThemes";

/* ── Shell ────────────────────────────────────────────────── */

export function SurveyShell({
  theme,
  preview = false,
  style,
  children,
}: PropsWithChildren<{ theme: SurveyTheme; preview?: boolean; style?: CSSProperties }>) {
  return (
    <div
      className={`survey-shell${preview ? " survey-theme-preview" : ""}`}
      data-survey-skin={theme.skin}
      data-survey-align={theme.layout.align}
      style={{ ...buildSurveyThemeVars(theme), ...style }}
    >
      {children}
    </div>
  );
}

export function SurveyProgressHeader({
  studyName,
  answered,
  total,
}: {
  studyName: string;
  answered: number;
  total: number;
}) {
  const pct = total > 0 ? Math.round((answered / total) * 100) : 0;
  return (
    <div className="survey-header">
      <div className="survey-header-inner">
        <div className="survey-header-row">
          <div className="survey-header-brand">
            <span aria-hidden="true">✦</span>
            <span>{studyName}</span>
          </div>
          <span className="survey-label">
            {answered} / {total} respondidas
          </span>
        </div>
        <div className="survey-progress-track">
          <div className="survey-progress-fill" style={{ width: `${pct}%` }} />
        </div>
      </div>
    </div>
  );
}

/* ── Answer helpers ───────────────────────────────────────── */

export function hasAnswer(q: PublicFormQuestionRead, a: PublicAnswerCreate | undefined): boolean {
  if (!a) return false;
  switch (q.question_type) {
    case "text_short":
    case "text_long":
      return Boolean(a.value_text && a.value_text.trim());
    case "number":
      return a.value_number !== undefined && a.value_number !== null;
    case "date":
      return Boolean(a.value_date);
    case "multiple_choice":
      return Array.isArray(a.value_json) && a.value_json.length > 0;
    default:
      return Boolean(a.option_id);
  }
}

/* ── Question renderer ────────────────────────────────────── */

export function SurveyQuestionRenderer({
  question,
  answer,
  onChange,
}: {
  question: PublicFormQuestionRead;
  answer: PublicAnswerCreate | undefined;
  onChange: (patch: Partial<PublicAnswerCreate>) => void;
}) {
  const type = question.question_type;

  if (type === "likert" || type === "single_choice" || type === "dropdown" || type === "boolean") {
    const isLikert = type === "likert";
    return (
      <div
        role="radiogroup"
        className={isLikert ? "grid gap-2" : "flex flex-col gap-2"}
        style={isLikert ? { gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))" } : undefined}
      >
        {question.options.map((opt) => {
          const selected = answer?.option_id === opt.id;
          return (
            <button
              key={opt.id}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange({ option_id: opt.id })}
              className={`survey-option${selected ? " selected" : ""}${isLikert ? " survey-option--center" : ""}`}
            >
              <span className="survey-option-dot" aria-hidden="true" />
              <span>{opt.label}</span>
            </button>
          );
        })}
      </div>
    );
  }

  if (type === "multiple_choice") {
    const selected: string[] = Array.isArray(answer?.value_json) ? (answer!.value_json as string[]) : [];
    const toggle = (id: string) =>
      onChange({
        value_json: selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id],
      });
    return (
      <div role="group" className="flex flex-col gap-2">
        {question.options.map((opt) => {
          const isSel = selected.includes(opt.id);
          return (
            <button
              key={opt.id}
              type="button"
              role="checkbox"
              aria-checked={isSel}
              onClick={() => toggle(opt.id)}
              className={`survey-option${isSel ? " selected" : ""}`}
            >
              <span className="survey-option-dot" aria-hidden="true" />
              <span>{opt.label}</span>
            </button>
          );
        })}
      </div>
    );
  }

  if (type === "number") {
    return (
      <input
        type="number"
        className="survey-input"
        min={question.min_value ?? undefined}
        max={question.max_value ?? undefined}
        value={answer?.value_number ?? ""}
        onChange={(e) =>
          onChange({ value_number: e.target.value === "" ? null : Number(e.target.value) })
        }
      />
    );
  }

  if (type === "date") {
    return (
      <input
        type="date"
        className="survey-input"
        value={answer?.value_date ?? ""}
        onChange={(e) => onChange({ value_date: e.target.value || null })}
      />
    );
  }

  // text_short / text_long y cualquier otro
  if (type === "text_long") {
    return (
      <textarea
        rows={4}
        className="survey-textarea"
        placeholder="Escribe tu respuesta…"
        value={answer?.value_text ?? ""}
        onChange={(e) => onChange({ value_text: e.target.value })}
      />
    );
  }
  return (
    <input
      type="text"
      className="survey-input"
      placeholder="Escribe tu respuesta…"
      value={answer?.value_text ?? ""}
      onChange={(e) => onChange({ value_text: e.target.value })}
    />
  );
}

/* ── "Todo en una pantalla" ───────────────────────────────── */

export function SurveyAllQuestionsView({
  title,
  kicker,
  description,
  sections,
  answers,
  onAnswerChange,
  onSubmit,
  submitting,
  error,
}: {
  title: string;
  kicker: string;
  description?: string | null;
  sections: {
    id: string;
    title: string | null;
    description?: string | null;
    questions: PublicFormQuestionRead[];
  }[];
  answers: Record<string, PublicAnswerCreate>;
  onAnswerChange: (questionId: string, patch: Partial<PublicAnswerCreate>) => void;
  onSubmit: () => void;
  submitting: boolean;
  error: string | null;
}) {
  const allQuestions = sections.flatMap((s) => s.questions);
  const total = allQuestions.length;
  const answered = allQuestions.filter((q) => hasAnswer(q, answers[q.id])).length;
  const missing = allQuestions.filter((q) => q.is_required && !hasAnswer(q, answers[q.id]));

  let idx = 0;
  return (
    <div className="survey-all">
      <div className="survey-all-hero">
        <span className="survey-all-kicker">{kicker}</span>
        <h1 className="survey-all-title">{title}</h1>
        {description ? <p className="survey-all-description">{description}</p> : null}
      </div>

      {sections.map((section) => (
        <div key={section.id}>
          {section.title ? (
            <div className="survey-section-banner survey-all-section-banner">
              <p className="survey-section-title">{section.title}</p>
              {section.description ? (
                <p className="survey-section-description">{section.description}</p>
              ) : null}
            </div>
          ) : null}
          {section.questions.map((question) => {
            idx += 1;
            const answer = answers[question.id];
            const isMissing = question.is_required && !hasAnswer(question, answer);
            return (
              <div key={question.id} className="survey-all-row">
                <div className="survey-grid">
                  <div>
                    <p className="survey-label">
                      Pregunta {idx} de {total}
                    </p>
                    {question.code ? <p className="survey-short-label">{question.code}</p> : null}
                  </div>
                  <div className="flex flex-col gap-4">
                    <p className="survey-question-text">
                      {question.label}
                      {question.is_required ? " *" : ""}
                    </p>
                    {question.help_text ? (
                      <p className="survey-short-label">{question.help_text}</p>
                    ) : null}
                    <SurveyQuestionRenderer
                      question={question}
                      answer={answer}
                      onChange={(patch) => onAnswerChange(question.id, patch)}
                    />
                    {isMissing ? (
                      <p className="survey-required-note">Esta pregunta es obligatoria.</p>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ))}

      <div className="survey-all-footer">
        <div className="flex flex-col gap-1">
          <span className="survey-all-note">
            {answered} / {total} respondidas
          </span>
          {missing.length > 0 ? (
            <span className="survey-all-missing">Faltan {missing.length} obligatoria(s)</span>
          ) : null}
          {error ? <span className="survey-error-note">{error}</span> : null}
        </div>
        <button
          type="button"
          className="survey-btn survey-btn-primary survey-btn--wide"
          onClick={onSubmit}
          disabled={submitting || missing.length > 0}
        >
          {submitting ? "Enviando…" : "Enviar"}
        </button>
      </div>
    </div>
  );
}
