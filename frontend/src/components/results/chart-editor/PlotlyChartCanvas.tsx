import Plot from "react-plotly.js";

export default function PlotlyChartCanvas({
  data,
  layout,
  config,
  onReady,
}: {
  data: Record<string, unknown>[];
  layout: Record<string, unknown>;
  config: Record<string, unknown>;
  onReady?: (graphDiv: unknown) => void;
}) {
  return (
    <Plot
      config={config as never}
      data={data as never}
      layout={{ autosize: true, ...layout } as never}
      onInitialized={(_figure: unknown, graphDiv: unknown) => onReady?.(graphDiv)}
      onUpdate={(_figure: unknown, graphDiv: unknown) => onReady?.(graphDiv)}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
    />
  );
}
