import { Input } from "../../ui/Input";

export function ChartTextControls({
  title,
  subtitle,
  xAxisTitle,
  yAxisTitle,
  onChange,
}: {
  title: string;
  subtitle: string;
  xAxisTitle: string;
  yAxisTitle: string;
  onChange: (field: "title" | "subtitle" | "xAxisTitle" | "yAxisTitle", value: string) => void;
}) {
  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Etiquetas</h4>
      <div className="space-y-2">
        <label className="text-sm font-medium text-dark">Titulo</label>
        <Input value={title} onChange={(event) => onChange("title", event.target.value)} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-dark">Subtitulo</label>
        <Input value={subtitle} onChange={(event) => onChange("subtitle", event.target.value)} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-dark">Eje X</label>
        <Input value={xAxisTitle} onChange={(event) => onChange("xAxisTitle", event.target.value)} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-dark">Eje Y</label>
        <Input value={yAxisTitle} onChange={(event) => onChange("yAxisTitle", event.target.value)} />
      </div>
    </div>
  );
}
