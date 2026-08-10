import { BarChart3 } from "lucide-react";

import type { QuestionDescriptive } from "../../types/analysis";
import { QuestionChartCard } from "./QuestionChartCard";

/** Preguntas que tienen algo que graficar: categorías o resumen numérico. */
function isChartable(question: QuestionDescriptive): boolean {
  return question.frequencies.length > 0 || Boolean(question.numeric);
}

export function TelemetryChartsGrid({
  questions,
  formId,
}: {
  questions: QuestionDescriptive[];
  formId: string;
}) {
  const chartable = questions.filter(isChartable);

  if (chartable.length === 0) {
    return (
      <section className="flex flex-col items-center justify-center rounded-[24px] border border-dashed border-border bg-white px-6 py-16 text-center shadow-card">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber/10 text-amber">
          <BarChart3 className="h-8 w-8" />
        </div>
        <h3 className="text-lg font-semibold text-dark">Aún no hay datos para graficar</h3>
        <p className="mt-2 max-w-md text-sm text-muted">
          En cuanto tus participantes respondan el formulario, aquí verás los gráficos de cada
          pregunta actualizándose en vivo.
        </p>
      </section>
    );
  }

  return (
    <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {chartable.map((question) => (
        <QuestionChartCard key={question.question_id} question={question} formId={formId} />
      ))}
    </div>
  );
}
