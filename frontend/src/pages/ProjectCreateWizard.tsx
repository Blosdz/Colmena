import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Rocket,
  Loader2,
  AlertTriangle,
  Sparkles,
  ArrowLeft,
  ArrowRight,
  FolderPlus,
} from "lucide-react";

import { VariableTreeSidebar } from "../components/project/VariableTreeSidebar";
import { Select, SelectOption } from "../components/ui/Select";
import { VariableSettingsPanel } from "../components/forms/VariableSettingsPanel";
import { ItemsPanel } from "../components/forms/ItemsPanel";
import { DimensionAssignmentPanel } from "../components/forms/DimensionAssignmentPanel";
import { BaremoAutoBuilder } from "../components/forms/BaremoAutoBuilder";
import { ExcelDataUploader } from "../components/forms/ExcelDataUploader";
import { ParticipantDataPanel } from "../components/project/ParticipantDataPanel";
import {
  PARTICIPANT_PRESETS,
  VARIABLE_PRESETS,
  exogenousOptionsFromPreset,
} from "../components/forms-wizard/scalePresets";
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
import { resolveDefaultCatalogScale } from "../utils/resolveDefaultScale";
import type { ParsedQuestion } from "../utils/bulkQuestionParser";
import { apiClient } from "../api/client";
import { useScales } from "../hooks/useScales";
import { createScale } from "../api/scales";
import type { CatalogScale } from "../components/forms/BulkQuestionTable";

// API imports for database sync
import {
  createProject,
  getProject,
  listProjects,
  createProjectVariable,
  updateProjectVariable,
  listProjectVariables,
} from "../api/projects";
import {
  createForm,
  createInstrument,
  createDimension,
  createQuestion,
  createQuestionOption,
  createSection,
  listSections,
  listProjectForms,
  listQuestions,
  listInstruments,
  listDimensions,
  listQuestionOptions,
  publishForm,
} from "../api/forms";

const TAB_LABELS: Record<VariableTab, string> = {
  variable: "Variable",
  dimensions: "Dimensiones",
  items: "Ítems",
  scale: "Escala",
  baremos: "Baremos",
  data: "Base de datos",
  participants: "Datos del participante",
};

// La escala se fusionó dentro de "items" (editor colapsable), ya no es una pestaña propia.
const VAR_TABS: VariableTab[] = ["variable", "dimensions", "items", "baremos"];

// Roles legacy que aún pueden venir de proyectos guardados antes de la simplificación.
function normalizeVariableRole(raw: string | undefined | null): VariableDraft["variableRole"] {
  if (raw === "main" || raw === "intervening") return raw;
  if (raw === "demographic" || raw === "sociodemografica") return "intervening";
  return "main";
}

export function ProjectCreateWizard() {
  const navigate = useNavigate();
  const { projectId: routeProjectId } = useParams();
  const store = useProjectDraft();
  const { draft, activeVariable, activeTab, showProjectInfo } = store;
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const isNewProject = !routeProjectId || routeProjectId === "new";
  const projectsQuery = useQuery({
    queryKey: ["project-selector-list"],
    queryFn: listProjects,
    enabled: isNewProject,
  });
  const existingProjects = projectsQuery.data?.items ?? [];

  // Catálogo de escalas del backend (fuente única de verdad; new project → solo presets del sistema)
  const scalesQuery = useScales(isNewProject ? undefined : routeProjectId);
  const catalogScales: CatalogScale[] = (scalesQuery.data?.items ?? []).map((s) => ({
    id: s.id,
    name: s.name,
    scale_kind: s.scale_kind,
    points: s.points,
    project_id: s.project_id,
    render_style: s.render_style,
    options: s.options.map((o) => ({ value: o.value, label: o.label })),
  }));
  // La escala global de la variable actúa como escala heredada por defecto de sus ítems.
  const defaultScale: CatalogScale | undefined =
    activeVariable.scale.options.length > 0
      ? {
          id: "__variable__",
          name: activeVariable.scale.name,
          options: activeVariable.scale.options.map((o) => ({ value: o.value, label: o.label })),
        }
      : undefined;

  // Backfill: si alguna variable arrancó sin escala (antes de que cargue el catálogo, o el
  // fallback vacío de createVariable/createDefaultDraft), se completa con la escala por defecto
  // del backend en cuanto el catálogo esté disponible. Nunca se hardcodea texto Likert aquí.
  useEffect(() => {
    if (!scalesQuery.data) return;
    const fallback = resolveDefaultCatalogScale(catalogScales);
    if (!fallback) return;
    draft.variables.forEach((v) => {
      if (v.scale.options.length === 0) {
        store.updateScale(v.id, {
          name: fallback.name,
          options: fallback.options.map((o, i) => ({ id: String(i + 1), value: o.value, label: o.label })),
          catalogScaleId: fallback.id,
        });
      }
    });
    // Depende también de `draft` completo (no solo de scalesQuery.data): `store.hydrate(...)`
    // reemplaza el objeto entero, y puede terminar después de que el catálogo ya cargó, trayendo
    // variables nuevas con escala vacía que también hay que backfillear. El cuerpo es idempotente
    // (solo toca variables con options.length === 0), así que re-ejecutar en cada cambio es barato.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scalesQuery.data, draft]);

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
        const projectVariablesResponse = await listProjectVariables(projId);

        const variables: VariableDraft[] = [];
        const participantFieldSet = new Set<string>();

        for (const form of formsResponse.items) {
          // Repoblar los checkboxes de "Datos del participante" desde sus preguntas
          const formQuestionsResponse = await listQuestions(form.id);
          for (const q of formQuestionsResponse.items) {
            if (q.question_role !== "sociodemographic") continue;
            const presetId = (q.config_json as { preset_id?: string } | null)?.preset_id;
            const preset =
              PARTICIPANT_PRESETS.find((p) => p.id === presetId) ||
              PARTICIPANT_PRESETS.find((p) => p.code === q.code);
            if (preset) participantFieldSet.add(preset.id);
          }

          const instrumentsResponse = await listInstruments(form.id);
          for (const instrument of instrumentsResponse.items) {
            // Match the study variable that backs this instrument (by id, fallback by name)
            const studyVar =
              projectVariablesResponse.items.find(v => v.id === instrument.project_variable_id) ||
              projectVariablesResponse.items.find(
                v => v.name.trim().toLowerCase() === instrument.name.trim().toLowerCase()
              );
            const dimsResponse = await listDimensions(instrument.id);
            const questionsResponse = await listQuestions(form.id);
            
            const psychQuestions = questionsResponse.items.filter(
              q =>
                q.instrument_id === instrument.id &&
                q.question_role !== "exogenous" &&
                q.question_role !== "sociodemographic"
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
                isImportance: false,
                type: q.question_type,
                scale: "Likert",
                status: "ready"
              });
            }
            
            // Rehidratar variables exógenas (form-wide, sin instrumento) en la
            // primera variable del formulario, para no perderlas al re-guardar.
            if (instrumentsResponse.items[0]?.id === instrument.id) {
              const exoQuestions = questionsResponse.items.filter(
                (q) => q.question_role === "exogenous",
              );
              for (const q of exoQuestions) {
                const exoOpts = await listQuestionOptions(q.id);
                items.push({
                  id: q.id,
                  text: q.label,
                  code: q.code || "",
                  dimensionName: "",
                  reversed: false,
                  required: q.is_required,
                  scored: false,
                  isImportance: false,
                  type: q.question_type,
                  scale: "",
                  status: "ready",
                  responseKind: "exogenous",
                  exogenousType:
                    q.question_type === "number"
                      ? "number"
                      : q.question_type === "text_short"
                        ? "text_short"
                        : "single_choice",
                  exogenousOptions: exoOpts.items.map((o) => ({
                    label: o.label,
                    value: parseFloat(o.value) || 0,
                  })),
                });
              }
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
              code: studyVar?.code || "",
              description: studyVar?.description || "",
              variableRole: normalizeVariableRole(studyVar?.variable_role),
              variableClassification: (studyVar?.variable_classification as VariableDraft["variableClassification"]) ?? null,
              measurementMode: (studyVar?.measurement_mode as VariableDraft["measurementMode"]) || "instrument",
              measurementLevel: (studyVar?.measurement_level as VariableDraft["measurementLevel"]) || "ordinal",
              dataType: (studyVar?.data_type as VariableDraft["dataType"]) || "numeric",
              isRequiredForAnalysis: studyVar?.is_required_for_analysis ?? true,
              dimensions: dimensionsDrafts,
              items,
              scale:
                scale.options.length > 0
                  ? scale
                  : (() => {
                      const fallback = resolveDefaultCatalogScale(catalogScales);
                      return fallback
                        ? {
                            name: fallback.name,
                            options: fallback.options.map((o, i) => ({ id: String(i + 1), value: o.value, label: o.label })),
                            catalogScaleId: fallback.id,
                          }
                        : scale;
                    })(),
              baremos: varBaremos
            });
          }
        }
        
        if (variables.length === 0) {
          variables.push(createVariable("Variable 1"));
        }
        
        store.hydrate({
          title: project.title,
          author: project.advisor_name || "",
          description: project.notes || "",
          variables,
          participantFields: [...participantFieldSet],
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

    // 2. Delete questions (se recrean desde el borrador, exógenas incluidas —
    // el wizard las rehidrata al abrir un proyecto existente).
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

    // 4. Delete sections (evita duplicar "Datos del participante" al re-guardar)
    try {
      const sectionsResponse = await listSections(formId);
      for (const s of sectionsResponse.items) {
        await apiClient.delete(`/api/v1/form-sections/${s.id}`);
      }
    } catch (e) {
      console.warn("Error clearing sections:", e);
    }
  };

  // Crea la sección fija "Datos del participante" con una pregunta no puntuada por preset.
  const createParticipantSection = async (formId: string) => {
    if (draft.participantFields.length === 0) return;
    const section = await createSection(formId, {
      title: "Datos del participante",
      description: "Datos sociodemográficos del participante.",
      sort_order: 0,
    });
    let idx = 0;
    for (const presetId of draft.participantFields) {
      const preset = PARTICIPANT_PRESETS.find((p) => p.id === presetId);
      if (!preset) continue;
      const qType =
        preset.fieldType === "number" ? "number" : preset.fieldType === "select" ? "single_choice" : "text_short";
      const question = await createQuestion(formId, {
        section_id: section.id,
        label: preset.name,
        code: preset.code,
        question_type: qType,
        question_role: "sociodemographic",
        measurement_level: preset.measurementLevel,
        data_type: preset.dataType,
        is_required: true,
        is_scored: false,
        sort_order: idx,
        config_json: { source: "participant_panel", preset_id: preset.id },
      });
      if (qType === "single_choice") {
        const labels = preset.optionsText.split(",").map((s) => s.trim()).filter(Boolean);
        for (let i = 0; i < labels.length; i++) {
          // Valor numérico (1..n) para poder teclearlo en la grilla de captura manual.
          await createQuestionOption(question.id, { label: labels[i], value: String(i + 1), sort_order: i });
        }
      }
      idx++;
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
          title: draft.title || "Proyecto sin título",
          advisor_name: draft.author || "",
          notes: draft.description || ""
        });
      }

      setActiveProjectId(projectId);

      // Fetch existing forms and study variables (avoid duplicating on re-save)
      const existingFormsResponse = await listProjectForms(projectId);
      const existingVariablesResponse = await listProjectVariables(projectId);

      // 2. For each variable, create the study Variable, then Form, Instrument, Dimensions, and Questions
      for (let i = 0; i < draft.variables.length; i++) {
        const variable = draft.variables[i];
        setSavingStatus(`Registrando variable de estudio: ${variable.name}...`);

        // 2a. Create (or reuse) the study variable → project_variables
        const existingVar = existingVariablesResponse.items.find(
          v => v.name.trim().toLowerCase() === variable.name.trim().toLowerCase()
        );
        const variablePayload = {
          name: variable.name,
          code: variable.code || null,
          description: variable.description || null,
          variable_role: variable.variableRole,
          variable_classification: variable.variableClassification ?? null,
          measurement_mode: variable.measurementMode,
          measurement_level: variable.measurementLevel,
          data_type: variable.dataType,
          is_required_for_analysis: variable.isRequiredForAnalysis,
        };
        let projectVariableId: string;
        if (existingVar) {
          // Persist any edits to role / level / type on re-save
          const updated = await updateProjectVariable(existingVar.id, variablePayload);
          projectVariableId = updated.id;
        } else {
          const createdVar = await createProjectVariable(projectId, variablePayload);
          projectVariableId = createdVar.id;
          existingVariablesResponse.items.push(createdVar);
        }

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

        // 2a-bis. Sección fija "Datos del participante" (primero en cada formulario)
        setSavingStatus("Creando sección de datos del participante...");
        await createParticipantSection(formId);

        // 2b. Create Instrument (linked to the study variable)
        const instrument = await createInstrument(formId, {
          name: variable.name,
          acronym: (variable.code || variable.name).substring(0, 5).toUpperCase(),
          description: variable.description || variable.name,
          project_variable_id: projectVariableId,
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

        // 2c-bis. Resolve (reuse or create) the catalog scale for this variable, so the
        // number of Likert points chosen actually persists in `scales`/`scale_options`.
        let variableScaleId: string | null = null;
        if (variable.scale.options.length > 0) {
          if (variable.scale.catalogScaleId) {
            variableScaleId = variable.scale.catalogScaleId;
          } else {
            setSavingStatus(`Guardando escala de respuesta: ${variable.scale.name}...`);
            const createdScale = await createScale(projectId, {
              name: variable.scale.name,
              scale_kind: "personalizada",
              render_style: "radio",
              points: variable.scale.options.length,
              options: variable.scale.options.map((o, i) => ({
                value: o.value,
                label: o.label,
                sort_order: i,
              })),
            });
            variableScaleId = createdScale.id;
          }
        }

        // 2d. Create Questions and Options
        for (let qIdx = 0; qIdx < variable.items.length; qIdx++) {
          const item = variable.items[qIdx];
          setSavingStatus(`Guardando ítem ${qIdx + 1}/${variable.items.length} en la base de datos...`);
          const dimensionId = item.dimensionName ? dimensionIdMap[item.dimensionName] : undefined;

          // ── Variable exógena (Sexo, Edad…) ──
          // Como en COLMENA 2.0: la variable exógena se registra como su PROPIO
          // project_variable (role sociodemográfico, clasificación "segment",
          // medición directa) + una pregunta no puntuada ligada a ella y SIN
          // instrumento, para que sirva de segmento comparable en el análisis.
          if (item.responseKind === "exogenous") {
            const exoType = item.exogenousType ?? "single_choice";
            const exoName = item.text.trim() || item.code || `Variable exógena ${qIdx + 1}`;
            const exoDataType = exoType === "number" ? "numeric" : exoType === "text_short" ? "text" : "categorical";

            let exoVar = existingVariablesResponse.items.find(
              (v) => v.name.trim().toLowerCase() === exoName.toLowerCase(),
            );
            if (!exoVar) {
              exoVar = await createProjectVariable(projectId, {
                name: exoName,
                code: item.code || null,
                description: null,
                variable_role: "sociodemographic",
                variable_classification: "segment",
                measurement_mode: "direct",
                measurement_level: exoType === "number" ? "ratio" : "nominal",
                data_type: exoDataType,
                is_required_for_analysis: false,
              });
              existingVariablesResponse.items.push(exoVar);
            }

            const exoQuestion = await createQuestion(formId, {
              label: item.text,
              question_type: exoType,
              instrument_id: null,
              dimension_id: null,
              project_variable_id: exoVar.id,
              scale_id: null,
              measurement_level: exoType === "number" ? "ratio" : "nominal",
              data_type: exoDataType === "text" ? "text" : exoType === "number" ? "numeric" : "categorical",
              code: item.code || `X${qIdx + 1}`,
              help_text: "",
              question_role: "exogenous",
              is_required: item.required ?? true,
              is_scored: false,
              is_reverse_scored: false,
              sort_order: qIdx,
            });
            if (exoType === "single_choice") {
              const exoOptions = (item.exogenousOptions ?? []).filter((o) => o.label.trim());
              for (let optIdx = 0; optIdx < exoOptions.length; optIdx++) {
                await createQuestionOption(exoQuestion.id, {
                  label: exoOptions[optIdx].label,
                  value: String(exoOptions[optIdx].value),
                  score: exoOptions[optIdx].value,
                  sort_order: optIdx,
                });
              }
            }
            continue;
          }

          // ── Ítem del constructo (Likert) ──
          // Normalizar: 'radio' no es aceptado por el formulario público; usar 'likert'
          const mappedType = (item.type === "radio" ? "likert" : item.type) || "likert";

          const question = await createQuestion(formId, {
            label: item.text,
            question_type: mappedType,
            instrument_id: instrumentId,
            dimension_id: dimensionId || null,
            project_variable_id: projectVariableId,
            scale_id: variableScaleId,
            measurement_level: variable.measurementLevel,
            data_type: variable.dataType,
            code: item.code || `P${qIdx + 1}`,
            help_text: "",
            question_role: item.isImportance ? "importance" : "item",
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
            score_min: 0,
            score_max: 100,
          });

          for (const [bandIdx, band] of variable.baremos.entries()) {
            if (band.max < band.min) continue; // rango inválido: se omite en vez de abortar todo el guardado
            await apiClient.post(`/api/v1/scoring/configs/${config.id}/bands`, {
              label: band.name,
              min_value: band.min,
              max_value: band.max,
              color_hint: band.color,
              interpretation: band.description || "",
              severity_order: bandIdx + 1,
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
              score_min: 0,
              score_max: 100,
            });

            for (const [bandIdx, band] of dim.baremos.entries()) {
              if (band.max < band.min) continue; // rango inválido: se omite en vez de abortar todo el guardado
              await apiClient.post(`/api/v1/scoring/configs/${config.id}/bands`, {
                label: band.name,
                min_value: band.min,
                max_value: band.max,
                color_hint: band.color,
                interpretation: band.description || "",
                severity_order: bandIdx + 1,
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

  const handleAddQuickDimension = () => {
    const nextIndex = activeVariable.dimensions.length + 1;
    store.addDimension(activeVariable.id, `Dimensión ${nextIndex}`);
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
      isImportance: false,
      status: "review",
    };
    store.addItems(activeVariable.id, [newItem]);
  };

  const handleAddExogenousItem = () => {
    const nextIndex = activeVariable.items.length + 1;
    const sexo = VARIABLE_PRESETS.find((p) => p.id === "sexo");
    const newItem: ParsedQuestion = {
      id: crypto.randomUUID(),
      code: `X${nextIndex}`,
      text: sexo?.name ?? "Variable exógena",
      dimensionName: "",
      type: "single_choice",
      scale: "",
      reversed: false,
      required: true,
      scored: false,
      isImportance: false,
      status: "review",
      responseKind: "exogenous",
      exogenousType: "single_choice",
      exogenousOptions: sexo ? exogenousOptionsFromPreset(sexo) : [{ label: "Opción 1", value: 1 }],
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

  const handleRemoveItem = (id: string) => {
    store.removeItem(activeVariable.id, id);
    setSelectedIds((prev) => prev.filter((x) => x !== id));
  };

  const canPublish = (!isNewProject || draft.title.trim().length > 0) && draft.variables.some((v) => v.items.length > 0);

  const scaleMin = Math.min(...activeVariable.scale.options.map((o) => o.value), 1);
  const scaleMax = Math.max(...activeVariable.scale.options.map((o) => o.value), 5);

  const isVarTab = activeTab !== "data" && activeTab !== "participants";

  // Navegación secuencial entre pestañas de la variable (variable → dimensiones → ítems → baremos)
  const varTabIndex = isVarTab ? VAR_TABS.indexOf(activeTab) : -1;
  const prevTab = varTabIndex > 0 ? VAR_TABS[varTabIndex - 1] : null;
  const nextTab = varTabIndex >= 0 && varTabIndex < VAR_TABS.length - 1 ? VAR_TABS[varTabIndex + 1] : null;





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

      {/* ── Modal: nombre del proyecto ───────────────── */}
      {showProjectInfo && !isSaving && (
        <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm z-40 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white border border-colmena-border rounded-2xl p-6 shadow-xl animate-colmena-fade-in">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber/15 text-amber">
                <FolderPlus className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-dark">
                  {isNewProject ? "Nuevo proyecto" : "Información del proyecto"}
                </h2>
                <p className="text-xs text-muted">Escribe el nombre de tu proyecto de investigación.</p>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[10px] font-bold text-muted uppercase tracking-wide mb-1">
                  Nombre del proyecto *
                </label>
                <input
                  autoFocus
                  className="colmena-input w-full h-10 text-sm font-semibold"
                  placeholder="Ej. Autoestima y clima laboral"
                  value={draft.title}
                  onChange={(e) => store.updateProject({ title: e.target.value })}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && draft.title.trim().length > 0) {
                      store.setShowProjectInfo(false);
                    }
                  }}
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-muted uppercase tracking-wide mb-1">
                  Investigador
                </label>
                <input
                  className="colmena-input w-full h-9 text-sm"
                  placeholder="Nombre del investigador"
                  value={draft.author}
                  onChange={(e) => store.updateProject({ author: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-muted uppercase tracking-wide mb-1">
                  Descripción
                </label>
                <input
                  className="colmena-input w-full h-9 text-sm"
                  placeholder="Descripción breve (opcional)"
                  value={draft.description}
                  onChange={(e) => store.updateProject({ description: e.target.value })}
                />
              </div>

              {isNewProject && existingProjects.length > 0 && (
                <div className="pt-2 border-t border-colmena-border">
                  <label className="block text-[10px] font-bold text-muted uppercase tracking-wide mb-1">
                    O continuar un proyecto existente
                  </label>
                  <Select
                    className="!h-9 !w-full !text-sm !rounded-lg"
                    value=""
                    onChange={(e) => {
                      const selectedId = e.target.value;
                      if (selectedId) navigate(`/project/${selectedId}`);
                    }}
                  >
                    <SelectOption value="">Elegir proyecto existente…</SelectOption>
                    {existingProjects.map((project) => (
                      <SelectOption key={project.id} value={project.id}>
                        {project.title}
                      </SelectOption>
                    ))}
                  </Select>
                </div>
              )}
            </div>

            <div className="mt-5 flex gap-2">
              {(draft.title.trim().length > 0 || !isNewProject) && (
                <button
                  type="button"
                  onClick={() => store.setShowProjectInfo(false)}
                  className="flex-1 colmena-button-secondary text-sm font-semibold h-10"
                >
                  Cancelar
                </button>
              )}
              <button
                type="button"
                disabled={draft.title.trim().length === 0}
                onClick={() => store.setShowProjectInfo(false)}
                className="flex-1 colmena-button-primary text-sm font-semibold h-10 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isNewProject ? "Crear" : "Guardar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Body ─────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar tree */}
        <VariableTreeSidebar
          projectTitle={draft.title}
          variables={draft.variables}
          activeVariableId={store.activeVariableId}
          activeTab={activeTab}
          dataRowCount={draft.dataRows.length}
          participantFieldCount={draft.participantFields.length}
          onSelectNode={(varId, tab) => {
            store.setActiveVariableId(varId);
            store.setActiveTab(tab);
            setSelectedIds([]);
          }}
          onSelectDataTab={() => store.setActiveTab("data")}
          onSelectParticipants={() => store.setActiveTab("participants")}
          onAddVariable={() => store.addVariable(resolveDefaultCatalogScale(catalogScales))}
          onRemoveVariable={store.removeVariable}
          onRenameVariable={store.renameVariable}
          onShowProjectInfo={() => store.setShowProjectInfo(true)}
        />

        {/* Main panel */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Toolbar: tabs + publish */}
          <div className="flex items-center gap-2 px-3 py-1.5 border-b border-colmena-border bg-white shrink-0">
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
              {(isVarTab ? VAR_TABS : ([activeTab] as VariableTab[])).map((tab) => (
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
              {activeTab === "variable" && (
                <div className="overflow-y-auto h-full">
                  <VariableSettingsPanel
                    variable={activeVariable}
                    onChange={(updates) => store.updateVariableMeta(activeVariable.id, updates)}
                  />
                </div>
              )}

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
                <ItemsPanel
                  variable={activeVariable}
                  catalogScales={catalogScales}
                  defaultScale={defaultScale}
                  selectedIds={selectedIds}
                  onToggleSelect={handleToggleSelect}
                  onToggleAll={handleToggleAll}
                  onClearSelection={() => setSelectedIds([])}
                  onAddItems={handleDataParsed}
                  onUpdateItem={handleUpdateItem}
                  onRemoveItem={handleRemoveItem}
                  onAddManualItem={handleAddManualItem}
                  onAddExogenousItem={handleAddExogenousItem}
                  onAddQuickDimension={handleAddQuickDimension}
                  onUpdateScale={(scale) => store.updateScale(activeVariable.id, scale)}
                />
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

              {activeTab === "participants" && (
                <div className="overflow-y-auto h-full">
                  <ParticipantDataPanel
                    selected={draft.participantFields}
                    onToggle={(id) => store.toggleParticipantField(id)}
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

          {/* Footer: navegación secuencial entre pestañas de la variable */}
          {isVarTab && (
            <div className="flex items-center justify-between gap-2 px-4 py-2.5 border-t border-colmena-border bg-white shrink-0">
              {prevTab ? (
                <button
                  type="button"
                  onClick={() => store.setActiveTab(prevTab)}
                  className="colmena-button-secondary inline-flex items-center gap-1.5 text-xs font-semibold h-9 px-4"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  {TAB_LABELS[prevTab]}
                </button>
              ) : (
                <span />
              )}
              {nextTab ? (
                <button
                  type="button"
                  onClick={() => store.setActiveTab(nextTab)}
                  className="colmena-button-primary inline-flex items-center gap-1.5 text-xs font-semibold h-9 px-4"
                >
                  Siguiente paso: {TAB_LABELS[nextTab]}
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleCreateProject}
                  disabled={!canPublish || isSaving}
                  className="colmena-button-primary inline-flex items-center gap-1.5 text-xs font-semibold h-9 px-4 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Rocket className="w-3.5 h-3.5" />
                  Confirmar y Publicar
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
