import { StatusPill } from '../ui/StatusPill.jsx';

export function PageHeader({ eyebrow, title, description, actions, className = '' }) {
  return (
    <div className={`flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between animate-colmena-fade-in ${className}`}>
      <div className="min-w-0 space-y-1.5">
        {eyebrow ? <StatusPill label={eyebrow} tone="draft" /> : null}
        <div className="space-y-1">
          <h1 className="truncate text-2xl font-bold tracking-tight text-dark">{title}</h1>
          {description ? <p className="max-w-3xl text-sm leading-5 text-muted">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export default PageHeader;
