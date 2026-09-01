import { hasAnswerValue } from '../../../../utils/surveyAnswers.js';
import SurveyQuestionRenderer from './SurveyQuestionRenderer.jsx';

/**
 * Modo "todas las preguntas en pantalla": estructura tomada directo de
 * survey_squeleton/Likability Survey.dc.html — hero con título grande y
 * bloques de pregunta separados por líneas divisorias (`.survey-all-row`),
 * en vez de una tarjeta por pregunta. La navegación de PublicSurveyPage
 * (índice, Atrás/Continuar) no aplica acá: todo vive en `answers` y se
 * envía de una sola vez.
 */
export default function SurveyAllQuestionsView({ bundle, answers, onAnswerChange, onSubmit, submitting, error }) {
  const questions = bundle.questions;
  const total = questions.length;
  const answeredCount = Object.keys(answers).length;
  const missingRequired = questions.filter((question) => question.is_required && !hasAnswerValue(answers[question.id]));
  const sections = bundle.sections && bundle.sections.length ? bundle.sections : [{ id: 'all', title: null, questions }];

  let globalIndex = 0;

  return (
    <div className="survey-all">
      <div className="survey-all-hero">
        <span className="survey-all-kicker">{bundle.study_name}</span>
        <h1 className="survey-all-title">{bundle.survey_name}</h1>
        {bundle.survey_description ? <p className="survey-all-description">{bundle.survey_description}</p> : null}
      </div>

      {sections.map((section) => (
        <div key={section.id}>
          {section.title ? (
            <div className="survey-section-banner survey-all-section-banner">
              <p className="survey-section-title">{section.title}</p>
              {section.description ? <p className="survey-section-description">{section.description}</p> : null}
              {section.section_kind === 'EXOGENOUS' ? <span className="survey-section-tag">Dato de perfil · no modifica tu puntaje</span> : null}
            </div>
          ) : null}

          {section.questions.map((question) => {
            globalIndex += 1;
            const value = answers[question.id];
            const missing = question.is_required && !hasAnswerValue(value);
            return (
              <div key={question.id} className="survey-all-row">
                <div className="survey-grid">
                  <div>
                    <p className="survey-label">
                      Pregunta {globalIndex} de {total}
                    </p>
                    {question.short_label ? <p className="survey-short-label">{question.short_label}</p> : null}
                  </div>
                  <div className="flex flex-col gap-4">
                    <p className="survey-question-text">{question.question_text}</p>
                    <SurveyQuestionRenderer question={question} value={value} onChange={(next) => onAnswerChange(question.id, next)} />
                    {missing ? <p className="survey-required-note">Esta pregunta es obligatoria.</p> : null}
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
            {answeredCount} / {total} respondidas
          </span>
          {missingRequired.length > 0 ? <span className="survey-all-missing">Faltan {missingRequired.length} obligatoria(s)</span> : null}
          {error ? <span className="survey-error-note">{error}</span> : null}
        </div>
        <button
          type="button"
          className="survey-btn survey-btn-primary survey-btn--wide"
          onClick={onSubmit}
          disabled={submitting || missingRequired.length > 0}
        >
          {submitting ? 'Enviando...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
}
