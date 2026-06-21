import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Save, Eye, ArrowRight } from "lucide-react";

import { useActiveStudy } from "../components/study/useActiveStudy";
import { PageHeader } from "../components/layout/PageHeader";
import { BulkQuestionImporter } from "../components/forms/BulkQuestionImporter";
import { BulkQuestionTable } from "../components/forms/BulkQuestionTable";
import { DimensionAssignmentPanel } from "../components/forms/DimensionAssignmentPanel";
import { ScaleBuilder } from "../components/forms/ScaleBuilder";
import { BaremoAutoBuilder } from "../components/forms/BaremoAutoBuilder";
import type { ParsedQuestion } from "../utils/bulkQuestionParser";
import type { DimensionDraft, ScaleDraft } from "../utils/projectDraftStore";
import type { BaremoLevel } from "../utils/baremoCalculator";
import { calculateEqualRangeBaremos } from "../utils/baremoCalculator";

const TABS = [
  { id: "items" as const, label: "Ítems" },
  { id: "dimensions" as const, label: "Dimensiones" },
  { id: "scale" as const, label: "Escala" },
  { id: "baremos" as const, label: "Baremos" },
];

const DEFAULT_SCALE: ScaleDraft = {
  name: "Likert 5 puntos",
  options: [
    { id: "1", value: 1, label: "Totalmente en desacuerdo" },
    { id: "2", value: 2, label: "En desacuerdo" },
    { id: "3", value: 3, label: "Ni de acuerdo ni en desacuerdo" },
    { id: "4", value: 4, label: "De acuerdo" },
    { id: "5", value: 5, label: "Totalmente de acuerdo" },
  ],
};

export function ProjectFormPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const [activeTab, setActiveTab] = useState<"items" | "dimensions" | "scale" | "baremos">("items");
  const [questions, setQuestions] = useState<ParsedQuestion[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [dimensions, setDimensions] = useState<DimensionDraft[]>([]);
  const [scale, setScale] = useState<ScaleDraft>(DEFAULT_SCALE);
  const [baremos, setBaremos] = useState<BaremoLevel[]>([]);

  const scaleMin = Math.min(...scale.options.map(o => o.value), 1);
  const scaleMax = Math.max(...scale.options.map(o => o.value), 5);

  const handleDataParsed = (newQuestions: ParsedQuestion[]) => {
    setQuestions((prev) => [...prev, ...newQuestions]);
  };

  const updateQuestion = (id: string, updates: Partial<ParsedQuestion>) => {
    setQuestions((prev) => prev.map(q => q.id === id ? { ...q, ...updates } : q));
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const handleToggleAll = () => {
    setSelectedIds(prev => prev.length === questions.length ? [] : questions.map(q => q.id));
  };

  const handleAutoGenerate = (levels: number) => {
    const varBaremos = calculateEqualRangeBaremos(questions.length * scaleMin, questions.length * scaleMax, levels);
    setBaremos(varBaremos);
    setDimensions(prev => prev.map(dim => {
      const dimItems = questions.filter(i => i.dimensionName === dim.name).length;
      const dimBaremos = calculateEqualRangeBaremos(dimItems * scaleMin, dimItems * scaleMax, levels);
      return { ...dim, baremos: dimBaremos };
    }));
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between">
        <PageHeader
          title="Constructor del Instrumento"
          description="Diseña el formulario, asigna dimensiones y define las escalas."
        />
        <div className="flex items-center gap-2">
          <button className="colmena-button-sm-secondary">
            <Eye className="w-3.5 h-3.5 mr-1.5" />
            Preview
          </button>
          <button className="colmena-button-sm-primary">
            <Save className="w-3.5 h-3.5 mr-1.5" />
            Guardar
          </button>
          <Link to={`/project/${projectId}/telemetry`} className="colmena-button-sm-primary" style={{ background: "#1c1f24" }}>
            Continuar
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Link>
        </div>
      </div>

      <div className="rounded-xl bg-white border border-colmena-border shadow-card flex-1 flex flex-col overflow-hidden min-h-[500px]">
        {/* Pill tabs */}
        <div className="flex items-center gap-1 px-5 py-2 border-b border-colmena-border bg-colmena-bg shrink-0">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`colmena-pill-tab ${activeTab === tab.id ? "active" : ""}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          <div className="max-w-5xl animate-colmena-fade-in" key={activeTab}>
            {activeTab === "items" && (
              <div className="space-y-4">
                <BulkQuestionImporter onDataParsed={handleDataParsed} />
                <BulkQuestionTable
                  questions={questions}
                  selectedIds={selectedIds}
                  dimensions={dimensions}
                  defaultScaleName={scale.name}
                  onToggleSelect={handleToggleSelect}
                  onToggleAll={handleToggleAll}
                  onUpdate={updateQuestion}
                />
              </div>
            )}

            {activeTab === "dimensions" && (
              <DimensionAssignmentPanel
                dimensions={dimensions}
                items={questions}
                onAdd={(name) => setDimensions(prev => [...prev, { id: crypto.randomUUID(), name, description: "", itemCodes: [], baremos: [] }])}
                onRemove={(id) => setDimensions(prev => prev.filter(d => d.id !== id))}
                onUpdate={(id, updates) => setDimensions(prev => prev.map(d => d.id === id ? { ...d, ...updates } : d))}
              />
            )}

            {activeTab === "scale" && (
              <ScaleBuilder scale={scale} onChange={setScale} />
            )}

            {activeTab === "baremos" && (
              <BaremoAutoBuilder
                items={questions}
                scaleMin={scaleMin}
                scaleMax={scaleMax}
                dimensions={dimensions}
                baremos={baremos}
                onChange={setBaremos}
                onAutoGenerate={handleAutoGenerate}
                onDimensionBaremosChange={(dimId, b) => setDimensions(prev => prev.map(d => d.id === dimId ? { ...d, baremos: b } : d))}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
