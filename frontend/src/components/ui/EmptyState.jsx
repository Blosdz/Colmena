import { Inbox } from 'lucide-react';

export function EmptyState({ title, description, children }) {
  return (
    <div className="animate-colmena-fade-in rounded-2xl border border-dashed border-[#dfe2e6] bg-gradient-to-b from-[#fafbfc] to-white px-5 py-8 text-center">
      <div className="mx-auto max-w-lg space-y-3">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-[#f5f6f8] text-muted/40">
          <Inbox className="h-5 w-5" />
        </div>
        <div className="space-y-2">
          <h3 className="text-[16px] font-semibold text-dark">{title}</h3>
          <p className="text-[13px] leading-5 text-muted">{description}</p>
        </div>
        {children ? <div>{children}</div> : null}
      </div>
    </div>
  );
}

export default EmptyState;
