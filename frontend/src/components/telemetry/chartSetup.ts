// Registro mínimo de Chart.js para la Telemetría (solo lo que usamos: donut + barras).
// Mantener liviano el bundle: no importamos `chart.js/auto`.
import {
  ArcElement,
  BarController,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  DoughnutController,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PieController,
  PointElement,
  ScatterController,
  Tooltip,
} from "chart.js";

let registered = false;

/** Registra los componentes de Chart.js una sola vez (idempotente). */
export function ensureChartsRegistered() {
  if (registered) return;
  ChartJS.register(
    ArcElement,
    BarController,
    BarElement,
    CategoryScale,
    DoughnutController,
    LinearScale,
    LineController,
    LineElement,
    PieController,
    PointElement,
    ScatterController,
    Tooltip,
    Legend,
  );
  ChartJS.defaults.font.family =
    "'Inter', system-ui, -apple-system, sans-serif";
  ChartJS.defaults.color = "#6B7280"; // token `muted`
  registered = true;
}

// Paleta de Colmena (tokens de tailwind.config.js) usada para categorías.
export const COLMENA_PALETTE = [
  "#F5B21A", // amber / colmena.yellow
  "#11B7B2", // turquoise / teal
  "#FF6A2A", // orange / honey
  "#2563EB", // info
  "#059669", // success
  "#D99712", // yellowDark
  "#0C9897", // turquoiseDark
  "#6B7280", // muted
  "#DC2626", // danger
  "#1C1F24", // graphite
];
