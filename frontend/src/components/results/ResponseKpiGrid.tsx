import { Activity, CheckCircle2, Clock3, Flag, Users } from "lucide-react";

const iconWrap = [
  "bg-[#EEF2FF] text-[#4F63FF]",
  "bg-[#EAF9EF] text-success",
  "bg-[#FFF2E4] text-orange",
  "bg-[#EEF2FF] text-[#356DFF]",
  "bg-[#F5EFFF] text-[#8B5CF6]",
];

export type ResponseKpiCardConfig = {
  title: string;
  value: string | number;
  delta: string;
  hint: string;
  icon: typeof Users;
  tone?: string;
};

function KpiCard({
  title,
  value,
  delta,
  hint,
  icon: Icon,
  tone,
}: {
  title: string;
  value: string | number;
  delta: string;
  hint: string;
  icon: typeof Users;
  tone: string;
}) {
  const deltaTone = delta.startsWith("↓") ? "text-orange" : "text-success";

  return (
    <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-dark">{title}</p>
          <p className="text-[40px] font-semibold leading-none tracking-tight text-dark">{value}</p>
          <p className={`text-sm font-medium ${deltaTone}`}>{delta}</p>
          <p className="text-sm text-muted">{hint}</p>
        </div>
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-[18px] ${tone}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

export function ResponseKpiGridCards({ cards }: { cards: ResponseKpiCardConfig[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card, index) => (
        <KpiCard
          delta={card.delta}
          hint={card.hint}
          icon={card.icon}
          key={card.title}
          title={card.title}
          tone={card.tone ?? iconWrap[index] ?? iconWrap[0]}
          value={card.value}
        />
      ))}
    </div>
  );
}

export function ResponseKpiGrid() {
  const cards: ResponseKpiCardConfig[] = [
    { title: "Respuestas totales", value: "248", delta: "↑ 24%", hint: "vs. la semana anterior", icon: Users },
    { title: "Completitud promedio", value: "92%", delta: "↑ 6%", hint: "vs. la semana anterior", icon: CheckCircle2 },
    { title: "Tiempo promedio", value: "6m 42s", delta: "↓ 12%", hint: "vs. la semana anterior", icon: Clock3 },
    { title: "Tasa de finalización", value: "78%", delta: "↑ 8%", hint: "vs. la semana anterior", icon: Flag },
    { title: "Respuestas hoy", value: "18", delta: "↑ 5", hint: "vs. ayer", icon: Activity },
  ];

  return <ResponseKpiGridCards cards={cards} />;
}
