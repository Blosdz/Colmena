import { AlertTriangle } from "lucide-react";

export function ErrorState({
  title = "No se pudo cargar la información",
  message,
}: {
  title?: string;
  message: string;
}) {
  return (
    <div className="animate-colmena-fade-in rounded-2xl border border-danger/15 bg-gradient-to-r from-danger/5 to-transparent px-6 py-5">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-danger/10 text-danger">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div className="space-y-1 pt-0.5">
          <h3 className="text-[15px] font-semibold text-danger">{title}</h3>
          <p className="text-[13px] leading-6 text-dark/70">{message}</p>
        </div>
      </div>
    </div>
  );
}
