import '@testing-library/jest-dom/vitest';

// jsdom no implementa ResizeObserver; recharts::ResponsiveContainer lo requiere
// para medir el contenedor. Sin este stub, cualquier test que monte un gráfico
// (BarChart, ScatterChart) lanza ReferenceError antes de poder aserear nada.
if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

