import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Rocket,
  Loader2,
  AlertTriangle,
  Sparkles,
} from "lucide-react";

import { VariableTreeSidebar } from "../components/project/VariableTreeSidebar";
import { BulkQuestionImporter } from "../components/forms/BulkQuestionImporter";
import { BulkQuestionTable } from "../components/forms/BulkQuestionTable";
import { DimensionAssignmentPanel } from "../components/forms/DimensionAssignmentPanel";
import { ScaleBuilder } from "../components/forms/ScaleBuilder";
import { BaremoAutoBuilder } from "../components/forms/BaremoAutoBuilder";
import { ExcelDataUploader } from "../components/forms/ExcelDataUploader";
import {
  useProjectDraft,
  type VariableTab,
  type VariableDraft,
  type DimensionDraft,
  type ScaleDraft,
  type BaremoLevel,
  createVariable,
} from "../utils/projectDraftStore";
import { setActiveProjectId } from "../utils/activeProject";
import type { ParsedQuestion } from "../utils/bulkQuestionParser";
import { apiClient } from "../api/client";

// API imports for database sync
import { createProject, getProject } from "../api/projects";
import {
  createForm,
  createInstrument,
  createDimension,
  createQuestion,
  createQuestionOption,
  listProjectForms,
  listQuestions,
  listInstruments,
  listDimensions,
  listQuestionOptions,
  publishForm,
} from "../api/forms";

const TAB_LABELS: Record<VariableTab, string> = {
  dimensions: "Dimensiones",
  items: "Ítems",
  scale: "Escala",
  baremos: "Baremos",
  data: "Base de datos",
};

const VAR_TABS: VariableTab[] = ["dimensions", "items", "scale", "baremos"];

const DEFAULT_SCALE = {
  name: "Likert 5 puntos",
  options: [
    { id: "1", value: 1, label: "Totalmente en desacuerdo" },
    { id: "2", value: 2, label: "En desacuerdo" },
    { id: "3", value: 3, label: "Ni de acuerdo ni en desacuerdo" },
    { id: "4", value: 4, label: "De acuerdo" },
    { id: "5", value: 5, label: "Totalmente de acuerdo" },
  ],
};

export function ProjectCreateWizard() {
  const navigate = useNavigate();
  const { projectId: routeProjectId } = useParams();
  const store = useProjectDraft();
  const { draft, activeVariable, activeTab, showProjectInfo } = store;
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Database saving states
  const [isSaving, setIsSaving] = useState(false);
  const [savingStatus, setSavingStatus] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);

  // Hydration effect for existing project
  useEffect(() => {
    const loadProjectData = async (projId: string) => {
      setIsSaving(true);
      setSavingStatus("Cargando datos del proyecto científico...");
      try {
        const project = await getProject(projId);
        const formsResponse = await listProjectForms(projId);
        
        const variables: VariableDraft[] = [];
        
        for (const form of formsResponse.items) {
          const instrumentsResponse = await listInstruments(form.id);
          for (const instrument of instrumentsResponse.items) {
            const dimsResponse = await listDimensions(instrument.id);
            const questionsResponse = await listQuestions(form.id);
            
            const psychQuestions = questionsResponse.items.filter(
              q => q.instrument_id === instrument.id && q.question_role !== "exogenous"
            );
            
            const items: ParsedQuestion[] = [];
            let scale: ScaleDraft = { name: "Likert", options: [] };
            
            for (const q of psychQuestions) {
              const optsResponse = await listQuestionOptions(q.id);
              if (scale.options.length === 0 && optsResponse.items.length > 0) {
                scale = {
                  name: "Likert",
                  options: optsResponse.items.map(opt => ({
                    id: opt.id,
                    value: parseFloat(opt.value),
                    label: opt.label
                  })).sort((a, b) => a.value - b.value)
                };
              }
              
              const dimName = dimsResponse.items.find(d => d.id === q.dimension_id)?.name || "";
              
              items.push({
                id: q.id,
                text: q.label,
                code: q.code || "",
                dimensionName: dimName,
                reversed: q.is_reverse_scored,
                required: q.is_required,
                scored: q.is_scored,
                type: q.question_type,
                scale: "Likert",
                status: "ready"
              });
            }
            
            // Fetch scoring configs and bands
            const configs = await apiClient.get<{ items: any[] }>(`/api/v1/forms/${form.id}/scoring/configs`);
            
            let varBaremos: BaremoLevel[] = [];
            const dimensionsDrafts: DimensionDraft[] = [];
            
            const generalConfig = configs.items.find(
              c => c.target_variable === instrument.name || (!c.target_dimension_id && c.type === "sum")
            );
            
            if (generalConfig) {
              const bands = await apiClient.get<any[]>(`/api/v1/scoring/configs/${generalConfig.id}/bands`);
              varBaremos = bands.map(b => ({
                id: b.id || crypto.randomUUID(),
                name: b.name,
                min: b.min_score,
                max: b.max_score,
                color: b.color_hint || b.color || "#F5B21A",
                description: b.interpretation || ""
              }));
            }
            
            for (const d of dimsResponse.items) {
              const dimConfig = configs.items.find(c => c.target_dimension_id === d.id);
              let dimBaremos: BaremoLevel[] = [];
              if (dimConfig) {
                const bands = await apiClient.get<any[]>(`/api/v1/scoring/configs/${dimConfig.id}/bands`);
                dimBaremos = bands.map(b => ({
                  id: b.id || crypto.randomUUID(),
                  name: b.name,
                  min: b.min_score,
                  max: b.max_score,
                  color: b.color_hint || b.color || "#F5B21A",
                  description: b.interpretation || ""
                }));
              }
              
              dimensionsDrafts.push({
                id: d.id,
                name: d.name,
                description: d.description || "",
                itemCodes: items.filter(it => it.dimensionName === d.name).map(it => it.code),
                baremos: dimBaremos
              });
            }
            
            variables.push({
              id: instrument.id,
              name: instrument.name,
              dimensions: dimensionsDrafts,
              items,
              scale: scale.options.length > 0 ? scale : { ...DEFAULT_SCALE },
              baremos: varBaremos
            });
          }
        }
        
        if (variables.length === 0) {
          variables.push(createVariable("Variable principal"));
        }
        
        store.hydrate({
          title: project.title,
          author: project.advisor_name || "",
          description: project.notes || "",
          variables,
          dataRows: [],
          dataColumns: []
        });
        
        setIsSaving(false);
      } catch (err: any) {
        console.error("Error loading project structure:", err);
        setSaveError("Error al cargar la información del proyecto desde el servidor.");
        setIsSaving(false);
      }
    };

    if (routeProjectId && routeProjectId !== "new") {
      void loadProjectData(routeProjectId);
    } else {
      store.reset();
      store.setShowProjectInfo(true);
    }
  }, [routeProjectId]);

  const clearFormStructure = async (formId: string) => {
    // 1. Delete scoring configs
    try {
      const configs = await apiClient.get<{ items: any[] }>(`/api/v1/forms/${formId}/scoring/configs`);
      for (const config of configs.items) {
        await apiClient.delete(`/api/v1/scoring/configs/${config.id}`);
      }
    } catch (e) {
      console.warn("Error clearing scoring configs:", e);
    }

    // 2. Delete questions
    try {
      const qResponse = await listQuestions(formId);
      for (const q of qResponse.items) {
        await apiClient.delete(`/api/v1/form-questions/${q.id}`);
      }
    } catch (e) {
      console.warn("Error clearing questions:", e);
    }

    // 3. Delete instruments & dimensions
    try {
      const instResponse = await listInstruments(formId);
      for (const inst of instResponse.items) {
        const dimsResponse = await listDimensions(inst.id);
        for (const d of dimsResponse.items) {
          await apiClient.delete(`/api/v1/form-dimensions/${d.id}`);
        }
        await apiClient.delete(`/api/v1/form-instruments/${inst.id}`);
      }
    } catch (e) {
      console.warn("Error clearing instruments:", e);
    }
  };

  const handleCreateProject = async () => {
    setIsSaving(true);
    setSaveError(null);
    try {
      let projectId = routeProjectId;
      if (!projectId || projectId === "new") {
        // 1. Create Project
        setSavingStatus("Iniciando registro de proyecto científico...");
        const project = await createProject({
          title: draft.title || "Proyecto sin título",
          advisor_name: draft.author || "",
          notes: draft.description || "",
          demographics: { sample_size_planned: 100 }
        });
        projectId = project.id;
      } else {
        // Update Project
        setSavingStatus("Actualizando información del proyecto...");
        await apiClient.patch(`/api/v1/projects/${projectId}`, {
          title: draft.title,
          advisor_name: draft.author,
          notes: draft.description
        });
      }

      setActiveProjectId(projectId);

      // Fetch existing forms
      const existingFormsResponse = await listProjectForms(projectId);

      // 2. For each variable, create Form, Instrument, Dimensions, and Questions
      for (let i = 0; i < draft.variables.length; i++) {
        const variable = draft.variables[i];
        setSavingStatus(`Guardando constructo métrico para: ${variable.name}...`);

        let form = existingFormsResponse.items.find(f => f.title === variable.name) || existingFormsResponse.items[i];
        let formId = "";

        if (form) {
          formId = form.id;
          await apiClient.patch(`/api/v1/forms/${formId}`, {
            title: variable.name,
            description: draft.description || `Formulario para la variable ${variable.name}`
          });
          await clearFormStructure(formId);
        } else {
          // 2a. Create Form
          form = await createForm(projectId, {
            title: variable.name,
            description: draft.description || `Formulario automatizado para la variable ${variable.name}`,
            status: "draft",
          });
          formId = form.id;
        }

        // 2b. Create Instrument
        const instrument = await createInstrument(formId, {
          name: variable.name,
          acronym: variable.name.substring(0, 5).toUpperCase(),
          description: variable.name,
        });
        const instrumentId = instrument.id;

        // 2c. Create Dimensions
        const dimensionIdMap: Record<string, string> = {};
        for (const dim of variable.dimensions) {
          setSavingStatus(`Creando dimensión: ${dim.name}...`);
          const createdDim = await createDimension(instrumentId, {
            name: dim.name,
            description: dim.description,
          });
          dimensionIdMap[dim.name] = createdDim.id;
        }

        // 2d. Create Questions and Options
        for (let qIdx = 0; qIdx < variable.items.length; qIdx++) {
          const item = variable.items[qIdx];
          setSavingStatus(`Guardando ítem ${qIdx + 1}/${variable.items.length} en la base de datos...`);

          // Normalizar: 'radio' no es aceptado por el formulario público; usar 'likert'
          const mappedType = (item.type === "radio" ? "likert" : item.type) || "likert";
          const dimensionId = item.dimensionName ? dimensionIdMap[item.dimensionName] : undefined;

          const question = await createQuestion(formId, {
            label: item.text,
            question_type: mappedType,
            instrument_id: instrumentId,
            dimension_id: dimensionId || null,
            code: item.code || `P${qIdx + 1}`,
            help_text: "",
            is_required: item.required ?? true,
            is_scored: item.scored ?? true,
            is_reverse_scored: item.reversed ?? false,
            sort_order: qIdx,
          });

          // 2e. Create scale options for the question
          const optionsToCreate = variable.scale.options;
          for (let optIdx = 0; optIdx < optionsToCreate.length; optIdx++) {
            const opt = optionsToCreate[optIdx];
            await createQuestionOption(question.id, {
              label: opt.label,
              value: opt.value.toString(),
              score: opt.value,
              sort_order: optIdx,
            });
          }
        }

        // 2f. Create Scoring Configs and Baremos (Variable level)
        if (variable.baremos.length > 0) {
          setSavingStatus(`Configurando baremos de variable: ${variable.name}...`);
          const config = await apiClient.post<{ id: string }>(`/api/v1/forms/${formId}/scoring/configs`, {
            name: `Baremos Generales - ${variable.name}`,
            instrument_id: instrumentId,
            scoring_level: "instrument",
            aggregation_method: "sum",
            missing_policy: "allow_partial",
          });

          for (const band of variable.baremos) {
            await apiClient.post(`/api/v1/scoring/configs/${config.id}/bands`, {
              label: band.name,
              min_value: band.min,
              max_value: band.max,
              color_hint: band.color,
              interpretation: band.description || "",
              severity_order: 0,
            });
          }
        }

        // 2g. Create Scoring Configs and Baremos (Dimension level)
        for (const dim of variable.dimensions) {
          if (dim.baremos.length > 0) {
            setSavingStatus(`Configurando baremos de dimensión: ${dim.name}...`);
            const dimId = dimensionIdMap[dim.name];
            const config = await apiClient.post<{ id: string }>(`/api/v1/forms/${formId}/scoring/configs`, {
              name: `Baremos - ${dim.name}`,
              dimension_id: dimId,
              scoring_level: "dimension",
              aggregation_method: "sum",
              missing_policy: "allow_partial",
            });

            for (const band of dim.baremos) {
              await apiClient.post(`/api/v1/scoring/configs/${config.id}/bands`, {
                label: band.name,
                min_value: band.min,
                max_value: band.max,
                color_hint: band.color,
                interpretation: band.description || "",
                severity_order: 0,
              });
            }
          }
        }

        // 2h. Publish the form so it gets an accessible public URL right away
        if (variable.items.length > 0) {
          setSavingStatus(`Publicando formulario: ${variable.name}...`);
          await publishForm(formId);
        }
      }

      setSavingStatus("¡Estructura guardada con éxito!");
      setIsSaving(false);
      store.reset();
      navigate(`/project/${projectId}/link`);
      return;
    } catch (err: any) {
      console.error(err);
      setSaveError(err.response?.data?.detail || "Error al persistir el proyecto en el servidor de base de datos.");
      setIsSaving(false);
    }
  };

  const handleDataParsed = (newItems: ParsedQuestion[]) => {
    store.addItems(activeVariable.id, newItems);
  };

  const handleAddManualItem = () => {
    const nextIndex = activeVariable.items.length + 1;
    const newItem: ParsedQuestion = {
      id: crypto.randomUUID(),
      code: `P${nextIndex}`,
      text: "",
      dimensionName: "",
      type: "likert",
      scale: "",
      reversed: false,
      required: true,
      scored: true,
      status: "review",
    };
    store.addItems(activeVariable.id, [newItem]);
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const handleToggleAll = () => {
    setSelectedIds((prev) =>
      prev.length === activeVariable.items.length ? [] : activeVariable.items.map((q) => q.id),
    );
  };

  const handleUpdateItem = (id: string, updates: Partial<ParsedQuestion>) => {
    store.updateItem(activeVariable.id, id, updates);
  };

  const isNewProject = !routeProjectId || routeProjectId === "new";
  const canPublish = (!isNewProject || draft.title.trim().length > 0) && draft.variables.some((v) => v.items.length > 0);

  const scaleMin = Math.min(...activeVariable.scale.options.map((o) => o.value), 1);
  const scaleMax = Math.max(...activeVariable.scale.options.map((o) => o.value), 5);

  const isVarTab = activeTab !== "data";





  return (
    <div className="flex h-full flex-col animate-colmena-fade-in relative">
      {/* ── Futuristic Saving Overlay ───────────────── */}
      {isSaving && (
        <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="max-w-sm w-full bg-[#0D1117]/90 border border-[#F5B21A]/20 rounded-2xl p-6 text-center shadow-[0_0_40px_rgba(245,178,26,0.12)] relative overflow-hidden">
            <div className="absolute -top-10 -left-10 w-20 h-20 bg-[#F5B21A]/10 rounded-full blur-xl" />
            <div className="absolute -bottom-10 -right-10 w-20 h-20 bg-[#E09A0A]/10 rounded-full blur-xl" />

            <Loader2 className="w-12 h-12 text-[#F5B21A] animate-spin mx-auto mb-4 drop-shadow-[0_0_8px_rgba(245,178,26,0.3)]" />

            <h3 className="text-base font-bold text-white font-mono uppercase tracking-wider mb-1.5 flex items-center justify-center gap-1.5">
              <Sparkles className="w-4 h-4 text-[#F5B21A]" />
              Sincronización
            </h3>

            <p className="text-slate-300 text-xs font-mono bg-slate-900/60 p-3 rounded-lg border border-white/5 animate-pulse min-h-[40px] flex items-center justify-center">
              {savingStatus}
            </p>

            <div className="mt-4 flex justify-center gap-1">
              <span className="w-1 h-1 rounded-full bg-[#F5B21A] animate-ping" />
              <span className="w-1 h-1 rounded-full bg-[#F5B21A]/60" />
              <span className="w-1 h-1 rounded-full bg-[#F5B21A]/30" />
            </div>
          </div>
        </div>
      )}

      {/* ── Error Overlay ──────────── */}
      {saveError && (
        <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="max-w-sm w-full bg-[#0D1117] border border-red-500/30 rounded-2xl p-6 text-center shadow-[0_0_30px_rgba(239,68,68,0.12)]">
            <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white font-mono uppercase tracking-wider mb-1.5">Error</h3>
            <p className="text-red-300 text-xs bg-red-950/20 border border-red-900/50 p-3 rounded-lg mb-4">{saveError}</p>
            <div className="flex gap-2">
              <button onClick={() => setSaveError(null)} className="flex-1 colmena-button-secondary text-xs font-semibold h-9">Cancelar</button>
              <button onClick={handleCreateProject} className="flex-1 colmena-button-primary text-xs font-semibold h-9">Reintentar</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Body ─────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar tree */}
        <VariableTreeSidebar
          variables={draft.variables}
          activeVariableId={store.activeVariableId}
          activeTab={activeTab}
          dataRowCount={draft.dataRows.length}
          onSelectNode={(varId, tab) => {
            store.setActiveVariableId(varId);
            store.setActiveTab(tab);
            setSelectedIds([]);
          }}
          onSelectDataTab={() => store.setActiveTab("data")}
          onAddVariable={store.addVariable}
          onRemoveVariable={store.removeVariable}
          onRenameVariable={store.renameVariable}
          onShowProjectInfo={() => store.setShowProjectInfo(true)}
        />

        {/* Main panel */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Toolbar: project info + tabs + publish */}
          <div className="flex items-center gap-2 px-3 py-1.5 border-b border-colmena-border bg-white shrink-0">
            {/* Project fields inline */}
            {showProjectInfo && (
              <div className="flex items-center gap-2 pr-3 mr-2 border-r border-colmena-border shrink-0 animate-colmena-fade-in">
                <input
                  className="colmena-input h-7 text-[11px] w-40 font-semibold"
                  placeholder="Nombre del proyecto *"
                  value={draft.title}
                  onChange={(e) => store.updateProject({ title: e.target.value })}
                />
                <input
                  className="colmena-input h-7 text-[11px] w-28"
                  placeholder="Investigador"
                  value={draft.author}
                  onChange={(e) => store.updateProject({ author: e.target.value })}
                />
                <input
                  className="colmena-input h-7 text-[11px] w-36"
                  placeholder="Descripción"
                  value={draft.description}
                  onChange={(e) => store.updateProject({ description: e.target.value })}
                />
              </div>
            )}

            {/* Breadcrumb + tabs */}
            <div className="flex items-center gap-0.5 flex-1 min-w-0">
              {isVarTab && (
                <>
                  <span className="text-[10px] font-bold text-amber mr-1.5 truncate max-w-[100px]">
                    {activeVariable.name}
                  </span>
                  <span className="text-[10px] text-colmena-border mr-1">›</span>
                </>
              )}
              {(isVarTab ? VAR_TABS : (["data"] as VariableTab[])).map((tab) => (
                <button
                  key={tab}
                  onClick={() => store.setActiveTab(tab)}
                  className={`colmena-pill-tab ${activeTab === tab ? "active" : ""}`}
                >
                  {TAB_LABELS[tab]}
                </button>
              ))}
            </div>

            {/* Publish button */}
            <button
              onClick={handleCreateProject}
              disabled={!canPublish || isSaving}
              className="colmena-button-sm-primary inline-flex items-center gap-1 shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
              type="button"
            >
              <Rocket className="w-3 h-3" />
              Confirmar y Publicar
            </button>
          </div>

          {/* Content area — tight padding, no max-width */}
          <div className="flex-1 overflow-hidden px-4 py-3 bg-colmena-bg">
            <div className="animate-colmena-fade-in h-full flex flex-col" key={`${store.activeVariableId}-${activeTab}`}>
              {activeTab === "dimensions" && (
                <div className="overflow-y-auto h-full">
                  <DimensionAssignmentPanel
                    dimensions={activeVariable.dimensions}
                    items={activeVariable.items}
                    onAdd={(name) => store.addDimension(activeVariable.id, name)}
                    onRemove={(dimId) => store.removeDimension(activeVariable.id, dimId)}
                    onUpdate={(dimId, updates) => store.updateDimension(activeVariable.id, dimId, updates)}
                  />
                </div>
              )}

              {activeTab === "items" && (
                <div className="flex-1 min-h-0 flex flex-col gap-3">
                  <div className="flex items-center gap-2">
                    <div className="flex-1">
                      <BulkQuestionImporter onDataParsed={handleDataParsed} />
                    </div>
                    <button
                      type="button"
                      onClick={handleAddManualItem}
                      className="colmena-button-sm-primary shrink-0"
                    >
                      + Agregar ítem
                    </button>
                  </div>
                  <BulkQuestionTable
                    questions={activeVariable.items}
                    selectedIds={selectedIds}
                    dimensions={activeVariable.dimensions}
                    defaultScaleName={activeVariable.scale.name}
                    onToggleSelect={handleToggleSelect}
                    onToggleAll={handleToggleAll}
                    onUpdate={handleUpdateItem}
                  />
                </div>
              )}

              {activeTab === "scale" && (
                <div className="overflow-y-auto h-full">
                  <ScaleBuilder
                    scale={activeVariable.scale}
                    onChange={(scale) => store.updateScale(activeVariable.id, scale)}
                  />
                </div>
              )}

              {activeTab === "baremos" && (
                <div className="overflow-y-auto h-full">
                  <BaremoAutoBuilder
                    items={activeVariable.items}
                    scaleMin={scaleMin}
                    scaleMax={scaleMax}
                    dimensions={activeVariable.dimensions}
                    baremos={activeVariable.baremos}
                    onChange={(baremos) => store.updateBaremos(activeVariable.id, baremos)}
                    onAutoGenerate={(levels) => store.autoGenerateAllBaremos(activeVariable.id, levels)}
                    onDimensionBaremosChange={(dimId, baremos) =>
                      store.updateDimensionBaremos(activeVariable.id, dimId, baremos)
                    }
                  />
                </div>
              )}

              {activeTab === "data" && (
                <div className="overflow-y-auto h-full">
                  <ExcelDataUploader
                    columns={draft.dataColumns}
                    rows={draft.dataRows}
                    onDataLoaded={(columns, rows) => store.setData(columns, rows)}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
