import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

/**
 * Estructura tomada de survey_squeleton (grid label-rail + contenido, un
 * tipo de pregunta por bloque). El look viene de las clases `.survey-*`
 * (frontend/src/index.css), que leen variables CSS puestas por el
 * `.survey-shell` ancestro — así el mismo componente sirve para las dos
 * skins elegibles en el paso Formulario (SurveyThemePicker) sin
 * duplicar el árbol de preguntas.
 */
export default function SurveyQuestionRenderer({ question, value, onChange }) {
  switch (question.question_type) {
    case 'SINGLE_CHOICE':
    case 'LIKERT':
      return <ChoiceOptions question={question} value={value} onChange={onChange} multiple={false} />;
    case 'MULTIPLE_CHOICE':
      return <ChoiceOptions question={question} value={value} onChange={onChange} multiple />;
    case 'NUMBER':
      return <NumberInput question={question} value={value} onChange={onChange} />;
    case 'TEXT':
      return (
        <textarea
          rows={4}
          className="survey-textarea"
          value={value || ''}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Escribe tu respuesta…"
        />
      );
    case 'BOOLEAN':
      return <BooleanToggle value={value} onChange={onChange} />;
    case 'DATE':
      return (
        <input
          type="date"
          className="survey-input"
          value={value || ''}
          onChange={(event) => onChange(event.target.value)}
        />
      );
    case 'DATETIME':
      return (
        <input
          type="datetime-local"
          className="survey-input"
          value={value || ''}
          onChange={(event) => onChange(event.target.value)}
        />
      );
    case 'RANKING':
      return <RankingList question={question} value={value} onChange={onChange} />;
    default:
      return <p className="survey-required-note">Tipo de pregunta no soportado todavía.</p>;
  }
}

function ChoiceOptions({ question, value, onChange, multiple }) {
  const isLikert = question.question_type === 'LIKERT';
  const selected = multiple ? value || [] : value;

  const toggle = (optionId) => {
    if (!multiple) {
      onChange(optionId);
      return;
    }
    const next = selected.includes(optionId)
      ? selected.filter((id) => id !== optionId)
      : [...selected, optionId];
    onChange(next);
  };

  return (
    <div
      className={isLikert ? 'grid gap-2' : 'flex flex-col gap-2'}
      style={isLikert ? { gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))' } : undefined}
      role={multiple ? 'group' : 'radiogroup'}
    >
      {question.options.map((option) => {
        const isSelected = multiple ? selected.includes(option.id) : selected === option.id;
        return (
          <button
            key={option.id}
            type="button"
            role={multiple ? 'checkbox' : 'radio'}
            aria-checked={isSelected}
            onClick={() => toggle(option.id)}
            className={`survey-option ${isSelected ? 'selected' : ''} ${isLikert ? 'survey-option--center' : ''}`}
          >
            <span className="survey-option-dot" aria-hidden="true" />
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}

function NumberInput({ question, value, onChange }) {
  const isNps = Boolean(question.validation_rules?.nps || question.validation_rules?.max >= 10);
  if (isNps) {
    const max = question.validation_rules?.max ?? 10;
    const min = question.validation_rules?.min ?? 0;
    return (
      <div className="flex flex-col gap-3">
        <div className="survey-nps-row">
          <span className="survey-nps-value">{value ?? min}</span>
        </div>
        <input
          type="range"
          min={min}
          max={max}
          value={value ?? min}
          onChange={(event) => onChange(Number(event.target.value))}
          className="survey-nps-range"
        />
        <div className="survey-nps-scale">
          <span>{min}</span>
          <span>{max}</span>
        </div>
      </div>
    );
  }
  return (
    <input
      type="number"
      className="survey-input"
      value={value ?? ''}
      onChange={(event) => onChange(event.target.value === '' ? null : Number(event.target.value))}
    />
  );
}

function BooleanToggle({ value, onChange }) {
  return (
    <div className="flex gap-3">
      {[
        { label: 'Sí', v: true },
        { label: 'No', v: false },
      ].map((opt) => (
        <button
          key={opt.label}
          type="button"
          onClick={() => onChange(opt.v)}
          className={`survey-toggle ${value === opt.v ? 'selected' : ''}`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function RankingList({ question, value, onChange }) {
  const [order] = useState(() => value || question.options.map((option) => option.id));
  const currentOrder = value || order;

  const move = (index, direction) => {
    const next = [...currentOrder];
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  };

  return (
    <div className="flex flex-col gap-2">
      {currentOrder.map((optionId, index) => {
        const option = question.options.find((o) => o.id === optionId);
        if (!option) return null;
        return (
          <div key={optionId} className="survey-rank-row">
            <span className="survey-rank-pos">{index + 1}. {option.label}</span>
            <div className="survey-rank-actions">
              <button type="button" onClick={() => move(index, -1)} className="survey-rank-btn" aria-label="Mover arriba">
                <ChevronUp size={14} />
              </button>
              <button type="button" onClick={() => move(index, 1)} className="survey-rank-btn" aria-label="Mover abajo">
                <ChevronDown size={14} />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
