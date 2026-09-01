import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Check } from 'lucide-react';

import { updateProject } from '../../../api/projects.js';
import {
  SURVEY_THEME_STYLES,
  EDITABLE_SURVEY_COLORS,
  QUESTIONS_PER_SCREEN_OPTIONS,
  ALIGN_OPTIONS,
  getSurveyThemeStyle,
  resolveSurveyTheme,
  buildSurveyThemeVars,
} from '../../../design/surveyThemes.js';
import { Button } from '../../ui/Button.jsx';
import SurveyProgressHeader from './take/SurveyProgressHeader.jsx';
import SurveyQuestionRenderer from './take/SurveyQuestionRenderer.jsx';
import SurveyAllQuestionsView from './take/SurveyAllQuestionsView.jsx';

const PREVIEW_QUESTIONS = [
  {
    id: 'preview-1',
    question_text: '¿Qué tan satisfecho quedaste con la experiencia?',
    short_label: 'Pregunta de ejemplo',
    question_type: 'SINGLE_CHOICE',
    is_required: true,
    options: [
      { id: 'opt-1', label: 'Muy satisfecho' },
      { id: 'opt-2', label: 'Satisfecho' },
      { id: 'opt-3', label: 'Neutral' },
    ],
  },
  {
    id: 'preview-2',
    question_text: 'El proceso se sintió claro de principio a fin.',
    short_label: 'Ejemplo de escala Likert',
    question_type: 'LIKERT',
    is_required: true,
    options: [
      { id: 'l-1', label: 'Muy en desacuerdo' },
      { id: 'l-2', label: 'En desacuerdo' },
      { id: 'l-3', label: 'Neutral' },
      { id: 'l-4', label: 'De acuerdo' },
      { id: 'l-5', label: 'Muy de acuerdo' },
    ],
  },
];

const PREVIEW_BUNDLE = {
  study_name: 'Vista previa',
  survey_name: 'Así se ve tu encuesta',
  survey_description: 'Todas las preguntas visibles en una sola pantalla, sin Atrás/Continuar.',
  questions: PREVIEW_QUESTIONS,
  sections: [],
};

/**
 * Elegir y editar la skin visual + el layout del formulario público (paso
 * Formulario del builder). Reusa los mismos componentes/clases `.survey-*`
 * que PublicSurveyPage para que el preview sea 1:1 con lo que verá el
 * encuestado — no una recreación aparte que se pueda desincronizar.
 *
 * Se guarda en `project.metadata.form_theme`, no en el `Survey` actual del
 * proyecto: cada vez que se "crea el formulario desde el instrumento"
 * (ProjectFormPage) se genera una fila de Survey nueva, y un Study ya
 * abierto al público puede seguir apuntando a una fila más vieja — si el
 * estilo viviera ahí, guardarlo no se reflejaría en el enlace público que
 * la gente realmente está usando.
 */
export default function SurveyThemePicker({ project }) {
  const queryClient = useQueryClient();
  const saved = resolveSurveyTheme(project.metadata?.form_theme);

  const [style, setStyle] = useState(saved.style);
  const [colors, setColors] = useState(saved.colors);
  const [layout, setLayout] = useState(saved.layout);
  const [previewAnswers, setPreviewAnswers] = useState({ 'preview-1': 'opt-1', 'preview-2': 'l-4' });

  const saveMutation = useMutation({
    mutationFn: () =>
      updateProject(project.id, {
        metadata: { ...(project.metadata || {}), form_theme: { style, colors, layout } },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', String(project.id)] });
    },
  });

  const handleSelectStyle = (styleId) => {
    if (styleId === style) return;
    setStyle(styleId);
    setColors(styleId === saved.style ? saved.colors : getSurveyThemeStyle(styleId).defaultColors);
  };

  const handleColorChange = (key, hex) => {
    setColors((prev) => ({ ...prev, [key]: hex }));
  };

  const handlePreviewAnswerChange = (questionId, value) => {
    setPreviewAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const isDirty =
    style !== saved.style ||
    layout.questionsPerScreen !== saved.layout.questionsPerScreen ||
    layout.align !== saved.layout.align ||
    EDITABLE_SURVEY_COLORS.some(({ key }) => colors[key] !== saved.colors[key]);

  const previewVars = { ...buildSurveyThemeVars({ colors }), minHeight: 'auto' };
  const isAllMode = layout.questionsPerScreen === 'all';

  return (
    <div className="flex flex-col gap-5">
      <div>
        <p className="colmena-label">Estilo del formulario</p>
        <p className="mt-1 text-xs text-muted">
          Elige cómo se ve la encuesta para quien la responde y ajusta sus colores. El cambio aplica al enlace público en cuanto lo guardas.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {Object.values(SURVEY_THEME_STYLES).map((option) => {
          const isSelected = style === option.id;
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => handleSelectStyle(option.id)}
              className={`flex flex-col gap-3 rounded-2xl border p-4 text-left transition-colors ${
                isSelected ? 'border-amber bg-amber/5' : 'border-border bg-white/60 hover:border-amber/40'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-dark">{option.label}</span>
                {isSelected ? (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber text-white">
                    <Check size={12} strokeWidth={3} />
                  </span>
                ) : null}
              </div>
              <p className="text-xs leading-5 text-muted">{option.description}</p>
              <div className="flex items-center gap-1.5">
                {Object.values(option.defaultColors).map((hex) => (
                  <span key={hex} className="h-4 w-4 rounded-full border border-black/10" style={{ background: hex }} />
                ))}
                <span className="ml-1 text-[11px] text-muted">Tipografía {option.fontLabel}</span>
              </div>
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {EDITABLE_SURVEY_COLORS.map(({ key, label }) => (
          <label key={key} className="flex items-center justify-between gap-3 rounded-xl border border-border bg-white/60 px-3 py-2">
            <span className="colmena-label">{label}</span>
            <input
              type="color"
              value={colors[key]}
              onChange={(event) => handleColorChange(key, event.target.value)}
              className="h-8 w-10 cursor-pointer rounded border border-border bg-transparent p-0"
            />
          </label>
        ))}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:gap-6">
        <div>
          <p className="colmena-label mb-2">Preguntas por pantalla</p>
          <div className="flex gap-1.5">
            {QUESTIONS_PER_SCREEN_OPTIONS.map((option) => (
              <button
                key={option.id}
                type="button"
                title={option.description}
                onClick={() => setLayout((prev) => ({ ...prev, questionsPerScreen: option.id }))}
                className={`colmena-pill-tab ${layout.questionsPerScreen === option.id ? 'active' : ''}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="colmena-label mb-2">Alineación</p>
          <div className="flex gap-1.5">
            {ALIGN_OPTIONS.map((option) => (
              <button
                key={option.id}
                type="button"
                onClick={() => setLayout((prev) => ({ ...prev, align: option.id }))}
                className={`colmena-pill-tab ${layout.align === option.id ? 'active' : ''}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div>
        <p className="colmena-label mb-2">Vista previa</p>
        <div className="overflow-hidden rounded-2xl border border-border">
          <div className="survey-shell survey-theme-preview" data-survey-skin={style} data-survey-align={layout.align} style={previewVars}>
            <SurveyProgressHeader studyName="Así lo verán tus encuestados" answered={1} total={2} />
            {isAllMode ? (
              <SurveyAllQuestionsView
                bundle={PREVIEW_BUNDLE}
                answers={previewAnswers}
                onAnswerChange={handlePreviewAnswerChange}
                onSubmit={() => {}}
                submitting={false}
                error={null}
              />
            ) : (
              <main className="survey-main">
                <div className="survey-card">
                  <div className="survey-grid">
                    <div>
                      <p className="survey-label">Pregunta 1 de 2</p>
                      <p className="survey-short-label">{PREVIEW_QUESTIONS[0].short_label}</p>
                    </div>
                    <div className="flex flex-col gap-4">
                      <p className="survey-question-text">{PREVIEW_QUESTIONS[0].question_text}</p>
                      <SurveyQuestionRenderer
                        question={PREVIEW_QUESTIONS[0]}
                        value={previewAnswers['preview-1']}
                        onChange={(value) => handlePreviewAnswerChange('preview-1', value)}
                      />
                    </div>
                  </div>
                </div>
                <div className="survey-footer">
                  <button type="button" className="survey-btn survey-btn-secondary">Atrás</button>
                  <button type="button" className="survey-btn survey-btn-primary survey-btn--wide">Continuar</button>
                </div>
              </main>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button variant="primary" onClick={() => saveMutation.mutate()} loading={saveMutation.isPending} disabled={!isDirty}>
          Guardar estilo
        </Button>
        {saveMutation.isSuccess && !isDirty ? <span className="text-xs font-medium text-turquoiseDark">Guardado</span> : null}
        {saveMutation.isError ? <span className="text-xs font-medium text-danger">No se pudo guardar. Intenta de nuevo.</span> : null}
      </div>
    </div>
  );
}
