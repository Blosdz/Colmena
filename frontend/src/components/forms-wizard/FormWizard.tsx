import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Copy } from "lucide-react";
import { Link } from "react-router-dom";

import {
  createDimension,
  createForm,
  createInstrument,
  createQuestion,
  createQuestionOption,
  createSection,
  getPublicLink,
  publishForm,
} from "../../api/forms";
import { createProjectVariable } from "../../api/projects";
import { createControlScale, createScoringConfig } from "../../api/scoring";
import type { PublicFormLink } from "../../types/form";
import { formatNumber } from "../../utils/formatters";
import { WorkspaceStepper } from "../layout/WorkspaceStepper";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { GlassCard } from "../ui/GlassCard";
import { SoftPanel } from "../ui/SoftPanel";
import { PrimaryAction } from "../ui/PrimaryAction";
import { StatusPill } from "../ui/StatusPill";
import { StepDimensions } from "./StepDimensions";
import { StepInstrument } from "./StepInstrument";
import { StepItems } from "./StepItems";
import { StepProjectContext } from "./StepProjectContext";
import { StepResponseScale } from "./StepResponseScale";
import { StepReviewPublish } from "./StepReviewPublish";
import { StepScoringRules } from "./StepScoringRules";
import { StepVariables } from "./StepVariables";
import { WizardNavigation } from "./WizardNavigation";

export type WizardVariableDraft = {
  id: string;
  name: string;
  code: string;
  role: string;
  measurementLevel: string;
  dataType: string;
  description: string;
  notes: string;
  requiredForAnalysis: boolean;
};

export type WizardInstrumentDraft = {
  name: string;
  acronym: string;
  author: string;
  year: string;
  description: string;
  variableId: string;
  responseScaleName: string;
  scoringMethod: string;
  reverseScoringEnabled: boolean;
};

export type WizardDimensionDraft = {
  id: string;
  name: string;
  code: string;
  description: string;
  sortOrder: number;
};

export type WizardItemDraft = {
  id: string;
  code: string;
  text: string;
  dimensionId: string;
  questionType: string;
  required: boolean;
  scored: boolean;
  reversed: boolean;
  sortOrder: number;
};

export type WizardScaleOptionDraft = {
  id: string;
  label: string;
  value: string;
  score: number;
  sortOrder: number;
};

export type WizardBaremDraft = {
  id: string;
  min: string;
  max: string;
  label: string;
  interpretation: string;
};

export type WizardLieScaleDraft = {
  enabled: boolean;
  name: string;
  code: string;
  controlType: string;
  ruleType: string;
  threshold: string;
  comparisonOperator: string;
  flagLevel: string;
  linkedItemCodes: string;
  message: string;
};

export type WizardFormContext = {
  title: string;
  description: string;
  instructions: string;
  thankYouMessage: string;
  allowAnonymous: boolean;
  status: string;
};

type WizardState = WizardFormContext & {
  variables: WizardVariableDraft[];
  instrument: WizardInstrumentDraft;
  dimensions: WizardDimensionDraft[];
  items: WizardItemDraft[];
  responseScale: WizardScaleOptionDraft[];
  scoringMethod: string;
  missingPolicy: string;
  minAnsweredItems: string;
  minCompletionPercent: string;
  scoreByDimension: boolean;
  totalScoreLabel: string;
  barems: WizardBaremDraft[];
  lieScale: WizardLieScaleDraft;
};

type WizardSubmitMode = "draft" | "publish";

type WizardSuccessState = {
  formId: string;
  publicLink: PublicFormLink | null;
  published: boolean;
  warnings: string[];
};

const stepLabels = [
  { key: "context", label: "Contexto" },
  { key: "variables", label: "Variables" },
  { key: "instrument", label: "Instrumento" },
  { key: "dimensions", label: "Dimensiones" },
  { key: "items", label: "Items" },
  { key: "scale", label: "Opciones" },
  { key: "scoring", label: "Scoring" },
  { key: "review", label: "Revision" },
];

const nextActionByStep: Record<string, string> = {
  context: "Definir variable",
  variables: "Agregar dimensiones",
  instrument: "Preparar dimensiones",
  dimensions: "Crear items",
  items: "Configurar escala",
  scale: "Configurar baremos",
  scoring: "Revisar estructura",
};

function createId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

function buildInitialState(): WizardState {
  return {
    title: "",
    description: "",
    instructions: "",
    thankYouMessage: "Gracias por completar el formulario.",
    allowAnonymous: true,
    status: "draft",
    variables: [
      {
        id: createId("var"),
        name: "",
        code: "",
        role: "resultado",
        measurementLevel: "ordinal",
        dataType: "numeric",
        description: "",
        notes: "",
        requiredForAnalysis: true,
      },
    ],
    instrument: {
      name: "",
      acronym: "",
      author: "",
      year: "",
      description: "",
      variableId: "",
      responseScaleName: "Likert 5 puntos",
      scoringMethod: "promedio",
      reverseScoringEnabled: false,
    },
    dimensions: [
      {
        id: createId("dim"),
        name: "Dimension 1",
        code: "D1",
        description: "",
        sortOrder: 0,
      },
    ],
    items: [
      {
        id: createId("item"),
        code: "item_01",
        text: "",
        dimensionId: "",
        questionType: "likert",
        required: true,
        scored: true,
        reversed: false,
        sortOrder: 0,
      },
    ],
    responseScale: [
      { id: createId("scale"), label: "Nunca", value: "1", score: 1, sortOrder: 0 },
      { id: createId("scale"), label: "Casi nunca", value: "2", score: 2, sortOrder: 1 },
      { id: createId("scale"), label: "A veces", value: "3", score: 3, sortOrder: 2 },
      { id: createId("scale"), label: "Casi siempre", value: "4", score: 4, sortOrder: 3 },
      { id: createId("scale"), label: "Siempre", value: "5", score: 5, sortOrder: 4 },
    ],
    scoringMethod: "mean",
    missingPolicy: "allow_partial",
    minAnsweredItems: "",
    minCompletionPercent: "70",
    scoreByDimension: true,
    totalScoreLabel: "Puntaje total",
    barems: [
      { id: createId("barem"), min: "1", max: "2.4", label: "Bajo", interpretation: "Nivel bajo" },
      { id: createId("barem"), min: "2.5", max: "3.6", label: "Medio", interpretation: "Nivel medio" },
      { id: createId("barem"), min: "3.7", max: "5", label: "Alto", interpretation: "Nivel alto" },
    ],
    lieScale: {
      enabled: false,
      name: "Escala de control",
      code: "control_scale",
      controlType: "lie",
      ruleType: "mean_threshold",
      threshold: "4",
      comparisonOperator: "gte",
      flagLevel: "warning",
      linkedItemCodes: "",
      message: "Revisar consistencia de respuestas si esta regla se activa.",
    },
  };
}

function slugify(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 60);
}

function parseOptionalNumber(value: string) {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseBands(barems: WizardBaremDraft[]) {
  return barems
    .map((barem, index) => ({
      label: barem.label.trim(),
      code: slugify(barem.label) || `band_${index + 1}`,
      min_value: parseOptionalNumber(barem.min),
      max_value: parseOptionalNumber(barem.max),
      interpretation: barem.interpretation.trim() || null,
      severity_order: index,
    }))
    .filter(
      (barem): barem is {
        label: string;
        code: string;
        min_value: number;
        max_value: number;
        interpretation: string | null;
        severity_order: number;
      } => Boolean(barem.label) && barem.min_value !== null && barem.max_value !== null,
    );
}

function parseLinkedCodes(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

async function copyText(value: string) {
  if (!navigator?.clipboard) {
    return;
  }
  await navigator.clipboard.writeText(value);
}

export function FormWizard({
  projectId,
  projectTitle,
}: {
  projectId: string;
  projectTitle?: string;
}) {
  const [stepIndex, setStepIndex] = useState(0);
  const [state, setState] = useState<WizardState>(buildInitialState());
  const [successState, setSuccessState] = useState<WizardSuccessState | null>(null);
  const [copyFeedback, setCopyFeedback] = useState("");
  const queryClient = useQueryClient();

  const currentStepKey = stepLabels[stepIndex]?.key ?? "context";

  const completedSteps = useMemo(() => {
    return [
      Boolean(state.title.trim()),
      state.variables.some((item) => item.name.trim()),
      Boolean(state.instrument.name.trim()),
      state.dimensions.some((item) => item.name.trim()),
      state.items.some((item) => item.text.trim()),
      state.responseScale.filter((item) => item.label.trim()).length >= 2,
      state.barems.some((item) => item.label.trim()),
      false,
    ];
  }, [state]);

  const canMoveForward = useMemo(() => {
    switch (currentStepKey) {
      case "context":
        return Boolean(state.title.trim());
      case "variables":
        return state.variables.some((item) => item.name.trim());
      case "instrument":
        return Boolean(state.instrument.name.trim());
      case "dimensions":
        return state.dimensions.some((item) => item.name.trim());
      case "items":
        return state.items.some((item) => item.text.trim());
      case "scale":
        return state.responseScale.filter((item) => item.label.trim()).length >= 2;
      case "scoring":
        return true;
      default:
        return true;
    }
  }, [currentStepKey, state]);

  const submitMutation = useMutation({
    mutationFn: async (mode: WizardSubmitMode) => {
      const createdForm = await createForm(projectId, {
        title: state.title,
        description: state.description,
        instructions: state.instructions,
        thank_you_message: state.thankYouMessage,
        allow_anonymous: state.allowAnonymous,
        status: "draft",
      });

      const section = await createSection(createdForm.id, {
        title: state.title || "Formulario principal",
        description: state.description || "Seccion generada desde el asistente de Colmena.",
        sort_order: 0,
      });

      const variableMap = new Map<string, string>();
      for (const variable of state.variables.filter((item) => item.name.trim())) {
        const created = await createProjectVariable(projectId, {
          name: variable.name,
          code: variable.code || null,
          description: variable.description || null,
          variable_role: variable.role,
          measurement_level: variable.measurementLevel,
          data_type: variable.dataType,
          is_required_for_analysis: variable.requiredForAnalysis,
          notes: variable.notes || null,
        });
        variableMap.set(variable.id, created.id);
      }

      const instrument = await createInstrument(createdForm.id, {
        name: state.instrument.name,
        project_variable_id: variableMap.get(state.instrument.variableId) ?? null,
        acronym: state.instrument.acronym || null,
        author: state.instrument.author || null,
        year: state.instrument.year ? Number(state.instrument.year) : null,
        description: state.instrument.description || null,
        response_scale_name: state.instrument.responseScaleName || null,
        scoring_method: state.scoringMethod,
        reverse_scoring_enabled: state.instrument.reverseScoringEnabled,
        sort_order: 0,
      });

      const dimensionMap = new Map<string, string>();
      for (const dimension of state.dimensions.filter((item) => item.name.trim())) {
        const created = await createDimension(instrument.id, {
          name: dimension.name,
          code: dimension.code || null,
          description: dimension.description || null,
          sort_order: dimension.sortOrder,
        });
        dimensionMap.set(dimension.id, created.id);
      }

      const scaleOptions = state.responseScale
        .filter((item) => item.label.trim())
        .map((item) => ({
          label: item.label,
          value: item.value || String(item.score),
          score: item.score,
          sort_order: item.sortOrder,
        }));

      const createdQuestionByCode = new Map<
        string,
        { questionId: string; dimensionId: string | null; optionIdsByScore: Map<number, string> }
      >();

      for (const item of state.items.filter((entry) => entry.text.trim())) {
        const createdQuestion = await createQuestion(createdForm.id, {
          section_id: section.id,
          instrument_id: instrument.id,
          dimension_id: dimensionMap.get(item.dimensionId) ?? null,
          code: item.code || null,
          label: item.text,
          question_type: item.questionType,
          question_role: "item",
          measurement_level: "ordinal",
          data_type: "numeric",
          is_required: item.required,
          is_scored: item.scored,
          is_reverse_scored: item.reversed,
          sort_order: item.sortOrder,
          config_json: {
            source: "form_wizard",
            response_scale: scaleOptions,
            scoring_rules: {
              aggregation_method: state.scoringMethod,
              missing_policy: state.missingPolicy,
              min_answered_items: parseOptionalNumber(state.minAnsweredItems),
              min_completion_percent: parseOptionalNumber(state.minCompletionPercent),
              score_by_dimension: state.scoreByDimension,
              total_score_label: state.totalScoreLabel,
              reverse_enabled: state.instrument.reverseScoringEnabled,
            },
          },
        });

        const optionIdsByScore = new Map<number, string>();
        for (const option of scaleOptions) {
          const createdOption = await createQuestionOption(createdQuestion.id, option);
          if (typeof option.score === "number") {
            optionIdsByScore.set(option.score, createdOption.id);
          }
        }
        if (item.code?.trim()) {
          createdQuestionByCode.set(item.code.trim(), {
            questionId: createdQuestion.id,
            dimensionId: dimensionMap.get(item.dimensionId) ?? null,
            optionIdsByScore,
          });
        }
      }

      const scoringWarnings: string[] = [];
      const scoredItems = state.items.filter((item) => item.text.trim() && item.scored);
      const parsedBands = parseBands(state.barems);

      if (scoredItems.length > 0) {
        try {
          const questionIds = scoredItems
            .map((item) => createdQuestionByCode.get(item.code.trim())?.questionId)
            .filter((item): item is string => Boolean(item));

          await createScoringConfig(createdForm.id, {
            instrument_id: instrument.id,
            name: state.totalScoreLabel.trim() || `Puntaje total ${state.instrument.name}`,
            code: slugify(state.totalScoreLabel || `${state.instrument.name}_total`) || "score_total",
            scoring_level: "instrument",
            aggregation_method: state.scoringMethod as "sum" | "mean" | "weighted_mean",
            missing_policy: state.missingPolicy as "strict_complete" | "allow_partial" | "prorate_if_threshold_met",
            min_answered_items: parseOptionalNumber(state.minAnsweredItems),
            min_completion_percent: parseOptionalNumber(state.minCompletionPercent),
            reverse_scoring_enabled: state.instrument.reverseScoringEnabled,
            interpretation_enabled: parsedBands.length > 0,
            config_json: {
              source: "form_wizard",
              question_ids: questionIds,
              question_codes: scoredItems.map((item) => item.code).filter(Boolean),
              score_by_dimension: state.scoreByDimension,
            },
            bands: parsedBands,
          });

          if (state.scoreByDimension) {
            for (const dimension of state.dimensions.filter((item) => item.name.trim())) {
              const dimensionQuestionIds = scoredItems
                .filter((item) => item.dimensionId === dimension.id)
                .map((item) => createdQuestionByCode.get(item.code.trim())?.questionId)
                .filter((item): item is string => Boolean(item));
              const persistedDimensionId = dimensionMap.get(dimension.id);
              if (!persistedDimensionId || dimensionQuestionIds.length === 0) {
                continue;
              }
              await createScoringConfig(createdForm.id, {
                instrument_id: instrument.id,
                dimension_id: persistedDimensionId,
                name: `${dimension.name} - puntaje`,
                code: slugify(`${dimension.code || dimension.name}_score`) || `dimension_${dimension.sortOrder + 1}`,
                scoring_level: "dimension",
                aggregation_method: state.scoringMethod as "sum" | "mean" | "weighted_mean",
                missing_policy: state.missingPolicy as "strict_complete" | "allow_partial" | "prorate_if_threshold_met",
                min_answered_items: parseOptionalNumber(state.minAnsweredItems),
                min_completion_percent: parseOptionalNumber(state.minCompletionPercent),
                reverse_scoring_enabled: state.instrument.reverseScoringEnabled,
                interpretation_enabled: parsedBands.length > 0,
                config_json: {
                  source: "form_wizard",
                  question_ids: dimensionQuestionIds,
                  question_codes: scoredItems
                    .filter((item) => item.dimensionId === dimension.id)
                    .map((item) => item.code)
                    .filter(Boolean),
                  score_scope: "dimension",
                },
                bands: parsedBands,
              });
            }
          }
        } catch (error) {
          scoringWarnings.push(
            error instanceof Error
              ? `No se pudieron guardar todas las reglas de scoring: ${error.message}`
              : "No se pudieron guardar todas las reglas de scoring.",
          );
        }
      } else {
        scoringWarnings.push("No se detectaron items puntuables para crear scoring avanzado.");
      }

      if (state.lieScale.enabled) {
        const linkedCodes = parseLinkedCodes(state.lieScale.linkedItemCodes);
        const controlItems = linkedCodes
          .map((code) => createdQuestionByCode.get(code))
          .filter((item): item is { questionId: string; dimensionId: string | null; optionIdsByScore: Map<number, string> } => Boolean(item))
          .map((item) => ({
            question_id: item.questionId,
            weight: 1,
          }));
        if (controlItems.length === 0) {
          scoringWarnings.push("La escala de control quedo activada, pero no se encontraron items asociados para guardarla.");
        } else {
          try {
            await createControlScale(createdForm.id, {
              instrument_id: instrument.id,
              name: state.lieScale.name.trim() || "Escala de control",
              code: slugify(state.lieScale.code || state.lieScale.name) || "control_scale",
              control_type: state.lieScale.controlType as "lie" | "attention" | "infrequency" | "consistency" | "custom",
              rule_type: state.lieScale.ruleType as "sum_threshold" | "mean_threshold" | "any_failed" | "count_failed" | "paired_inconsistency" | "custom",
              threshold: parseOptionalNumber(state.lieScale.threshold),
              comparison_operator: state.lieScale.comparisonOperator as "gt" | "gte" | "lt" | "lte" | "eq",
              flag_level: state.lieScale.flagLevel as "warning" | "invalid",
              message: state.lieScale.message.trim() || null,
              config_json: {
                source: "form_wizard",
                linked_item_codes: linkedCodes,
              },
              items: controlItems,
            });
          } catch (error) {
            scoringWarnings.push(
              error instanceof Error
                ? `No se pudo guardar la escala de control: ${error.message}`
                : "No se pudo guardar la escala de control.",
            );
          }
        }
      }

      let link: PublicFormLink | null = null;
      if (mode === "publish" || state.status === "published") {
        link = await publishForm(createdForm.id);
      } else {
        try {
          link = await getPublicLink(createdForm.id);
        } catch {
          link = null;
        }
      }

      return {
        formId: createdForm.id,
        publicLink: link,
        published: Boolean(link?.public_url),
        warnings: scoringWarnings,
      };
    },
    onSuccess: async (result) => {
      setSuccessState(result);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
        queryClient.invalidateQueries({ queryKey: ["project", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["project-forms", projectId] }),
      ]);
    },
  });

  const renderStep = () => {
    switch (currentStepKey) {
      case "context":
        return <StepProjectContext onChange={(next) => setState(next as WizardState)} value={state} />;
      case "variables":
        return <StepVariables onChange={(next) => setState(next as WizardState)} value={state} />;
      case "instrument":
        return <StepInstrument onChange={(next) => setState(next as WizardState)} value={state} />;
      case "dimensions":
        return <StepDimensions onChange={(next) => setState(next as WizardState)} value={state} />;
      case "items":
        return <StepItems onChange={(next) => setState(next as WizardState)} value={state} />;
      case "scale":
        return <StepResponseScale onChange={(next) => setState(next as WizardState)} value={state} />;
      case "scoring":
        return <StepScoringRules onChange={(next) => setState(next as WizardState)} value={state} />;
      case "review":
        return <StepReviewPublish projectTitle={projectTitle} value={state} />;
      default:
        return null;
    }
  };

  if (successState) {
    return (
      <div className="space-y-6">
        <GlassCard className="space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.14em] text-turquoiseDark">
                <CheckCircle2 className="h-4 w-4" />
                Formulario listo
              </p>
              <h2 className="text-3xl font-semibold tracking-tight text-graphite">
                {successState.published ? "Formulario publicado" : "Borrador guardado"}
              </h2>
              <p className="max-w-3xl text-sm leading-7 text-muted">
                Colmena ya creo la estructura del formulario, sus variables, dimensiones, items y escala base. El
                siguiente paso es compartir el enlace o entrar al detalle para revisar respuestas, scoring y resultados.
              </p>
            </div>
            <StatusPill label={successState.published ? "Publicado" : "Borrador"} tone={successState.published ? "published" : "draft"} />
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <SoftPanel className="space-y-4">
              <h3 className="text-lg font-semibold text-dark">Resumen del despliegue</h3>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-border bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Variables</p>
                  <p className="mt-2 text-2xl font-semibold text-dark">{formatNumber(state.variables.length, 0)}</p>
                </div>
                <div className="rounded-2xl border border-border bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Items</p>
                  <p className="mt-2 text-2xl font-semibold text-dark">{formatNumber(state.items.length, 0)}</p>
                </div>
                <div className="rounded-2xl border border-border bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Opciones</p>
                  <p className="mt-2 text-2xl font-semibold text-dark">{formatNumber(state.responseScale.length, 0)}</p>
                </div>
              </div>
            </SoftPanel>

            <SoftPanel className="space-y-4">
              <h3 className="text-lg font-semibold text-dark">Link publico</h3>
              {successState.publicLink?.public_url ? (
                <>
                  <div className="rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark">
                    {successState.publicLink.public_url}
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <Button
                      onClick={async () => {
                        await copyText(successState.publicLink?.public_url ?? "");
                        setCopyFeedback("Link copiado.");
                      }}
                      variant="secondary"
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      Copiar link
                    </Button>
                    <a
                      className="inline-flex h-11 items-center justify-center rounded-2xl bg-dark px-4 text-sm font-medium text-white"
                      href={successState.publicLink.public_url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      Abrir formulario publico
                    </a>
                  </div>
                  {copyFeedback ? <p className="text-sm text-success">{copyFeedback}</p> : null}
                </>
              ) : (
                <p className="text-sm text-muted">
                  El formulario quedo guardado como borrador. El siguiente paso es volver al proyecto para revisar la
                  estructura o publicarlo desde la etapa de link y respuestas.
                </p>
              )}
            </SoftPanel>
          </div>

          {successState.warnings.length > 0 ? (
            <SoftPanel className="space-y-2 border-warning/30 bg-[#fff8ec]">
              <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-warning">Revisiones sugeridas</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-dark">
                {successState.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </SoftPanel>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <Link
              className="inline-flex h-11 items-center justify-center rounded-2xl bg-dark px-4 text-sm font-medium text-white"
              to={`/project/${projectId}`}
            >
              Ir al proyecto
            </Link>
            <Link
              className="inline-flex h-11 items-center justify-center rounded-2xl bg-surfaceSoft px-4 text-sm font-medium text-dark"
              to={`/project/${projectId}/link`}
            >
              Publicar link
            </Link>
            <Button
              onClick={() => {
                setState(buildInitialState());
                setSuccessState(null);
                setStepIndex(0);
              }}
              variant="ghost"
            >
              Crear otro formulario
            </Button>
          </div>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <WorkspaceStepper
        currentKey={currentStepKey}
        steps={stepLabels.map((step, index) => ({ key: step.key, label: step.label, done: completedSteps[index] }))}
      />

      <GlassCard className="space-y-4 p-5 sm:p-6">
        {renderStep()}

        {submitMutation.isError ? (
          <ErrorState message={(submitMutation.error as Error).message} />
        ) : null}

        {currentStepKey === "review" ? (
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-5">
            <Button disabled={stepIndex === 0} onClick={() => setStepIndex((current) => Math.max(0, current - 1))} variant="secondary">
              Anterior
            </Button>
            <div className="flex flex-wrap gap-3">
              <Button loading={submitMutation.isPending} onClick={() => submitMutation.mutate("draft")} variant="secondary">
                Guardar borrador
              </Button>
              <PrimaryAction disabled={!canMoveForward} onClick={() => submitMutation.mutate("publish")}>
                Publicar formulario
              </PrimaryAction>
            </div>
          </div>
        ) : (
          <WizardNavigation
            backLabel="Anterior"
            canGoBack={stepIndex > 0}
            canGoNext={canMoveForward}
            nextLabel={nextActionByStep[currentStepKey] ?? "Siguiente etapa"}
            onBack={() => setStepIndex((current) => Math.max(0, current - 1))}
            onNext={() => setStepIndex((current) => Math.min(stepLabels.length - 1, current + 1))}
          />
        )}
      </GlassCard>
    </div>
  );
}
