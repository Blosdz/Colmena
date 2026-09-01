import { BrandMark } from '../../../../brand/BrandMark.jsx';

export default function SurveyProgressHeader({ studyName, answered, total }) {
  const pct = total > 0 ? Math.round((answered / total) * 100) : 0;

  return (
    <div className="survey-header">
      <div className="survey-header-inner">
        <div className="survey-header-row">
          <div className="survey-header-brand">
            <BrandMark className="h-4 w-4" />
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
