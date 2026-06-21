export function LoadingState({ label = "Cargando..." }: { label?: string }) {
  return (
    <div className="animate-colmena-fade-in flex items-center justify-center py-20">
      <div className="flex flex-col items-center gap-4">
        <div className="relative h-10 w-10">
          <div className="absolute inset-0 rounded-full border-[3px] border-[#eef0f3]" />
          <div className="absolute inset-0 rounded-full border-[3px] border-transparent border-t-amber animate-spin" />
        </div>
        <p className="text-[13px] font-medium text-muted">{label}</p>
      </div>
    </div>
  );
}
