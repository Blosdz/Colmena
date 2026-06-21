declare module "plotly.js/dist/plotly.min.js" {
  const Plotly: {
    toImage: (
      graphDiv: unknown,
      options: { format: "png" | "svg"; width: number; height: number; scale?: number },
    ) => Promise<string>;
  };

  export default Plotly;
}
