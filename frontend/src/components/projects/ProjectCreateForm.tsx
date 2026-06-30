import { useEffect, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import { listApproaches, listResearchTypes, type CatalogItem } from "../../api/catalogs";
import type { ProjectCreatePayload } from "../../types/project";
import { PrimaryAction } from "../ui/PrimaryAction";

type ProjectFormState = {
  title: string;
  type_research_id: string;
  approach_id: string;
  institution: string;
  faculty: string;
  career: string;
  sample_size_planned: number | null;
  population_description: string;
  author: string;
  intention: string;
  objective: string;
  mainVariable: string;
  secondaryVariables: string;
  instrumentReferences: string;
};

const initialState: ProjectFormState = {
  title: "",
  type_research_id: "",
  approach_id: "",
  institution: "",
  faculty: "",
  career: "",
  sample_size_planned: null,
  population_description: "",
  author: "",
  intention: "",
  objective: "",
  mainVariable: "",
  secondaryVariables: "",
  instrumentReferences: "",
};

type Props = {
  onSubmit: (payload: ProjectCreatePayload) => void;
  isLoading: boolean;
  collapsible?: boolean;
};

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="space-y-2">
      <span className="text-[13px] font-semibold text-dark">{label}</span>
      {children}
    </label>
  );
}

export function ProjectCreateForm({ onSubmit, isLoading, collapsible = true }: Props) {
  const [formState, setFormState] = useState<ProjectFormState>(initialState);
  const [isOpen, setIsOpen] = useState(!collapsible);
  const [researchTypes, setResearchTypes] = useState<CatalogItem[]>([]);
  const [approaches, setApproaches] = useState<CatalogItem[]>([]);

  useEffect(() => {
    listResearchTypes()
      .then((res) => setResearchTypes(res.items))
      .catch(() => setResearchTypes([]));
    listApproaches()
      .then((res) => setApproaches(res.items))
      .catch(() => setApproaches([]));
  }, []);

  const submit = () => {
    onSubmit({
      title: formState.title,
      type_research_id: formState.type_research_id || undefined,
      approach_id: formState.approach_id || undefined,
      institution: formState.institution,
      faculty: formState.faculty,
      career: formState.career,
      demographics: {
        population_description: formState.population_description || undefined,
        sample_size_planned: formState.sample_size_planned,
      },
    });
  };

  return (
    <div className="rounded-[28px] border border-border bg-white shadow-card">
      <div className="flex items-center justify-between gap-4 px-6 py-5">
        <div className="space-y-1">
          <h2 className="text-[18px] font-semibold text-dark">Crear proyecto</h2>
          <p className="text-sm text-muted">Define el contexto base del estudio.</p>
        </div>
        {collapsible ? (
          <button
            className="colmena-button-secondary inline-flex items-center gap-2"
            onClick={() => setIsOpen((current) => !current)}
            type="button"
          >
            Nuevo proyecto
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        ) : null}
      </div>

      {isOpen ? (
        <>
          <div className="border-t border-border px-6 py-6">
            <div className="mx-auto max-w-[1040px] space-y-6">
              <div className="space-y-1">
                <h3 className="text-[18px] font-semibold text-dark">Crear nuevo proyecto</h3>
                <p className="text-sm text-muted">Define la información básica de tu proyecto de investigación.</p>
              </div>

              <div className="rounded-[20px] border border-border px-5 py-5">
                <div className="mb-5 flex items-center gap-3">
                  <span className="h-5 w-1 rounded-full bg-amber" />
                  <h4 className="text-lg font-semibold text-dark">Información general</h4>
                </div>

                <div className="grid gap-5 md:grid-cols-2">
                  <Field label="Nombre del proyecto *">
                    <input
                      className="colmena-input w-full border border-border px-4"
                      placeholder="Ej. Satisfacción del cliente en servicios digitales"
                      value={formState.title}
                      onChange={(event) => setFormState((current) => ({ ...current, title: event.target.value }))}
                    />
                  </Field>
                  <Field label="Autor / Investigador principal *">
                    <input
                      className="colmena-input w-full border border-border px-4"
                      placeholder="Tu nombre completo"
                      value={formState.author}
                      onChange={(event) => setFormState((current) => ({ ...current, author: event.target.value }))}
                    />
                  </Field>

                  <Field label="Tipo de investigación *">
                    <select
                      className="colmena-input w-full border border-border bg-white px-4"
                      value={formState.type_research_id}
                      onChange={(event) =>
                        setFormState((current) => ({ ...current, type_research_id: event.target.value }))
                      }
                    >
                      <option value="">Seleccionar tipo de investigación</option>
                      {researchTypes.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Enfoque *">
                    <select
                      className="colmena-input w-full border border-border bg-white px-4"
                      value={formState.approach_id}
                      onChange={(event) =>
                        setFormState((current) => ({ ...current, approach_id: event.target.value }))
                      }
                    >
                      <option value="">Seleccionar enfoque</option>
                      {approaches.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </Field>

                  <Field label="Intención del proyecto">
                    <textarea
                      className="min-h-[104px] w-full rounded-[18px] border border-border px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/15"
                      placeholder="Ej. Comprender, evaluar, analizar o medir."
                      value={formState.intention}
                      onChange={(event) => setFormState((current) => ({ ...current, intention: event.target.value }))}
                    />
                  </Field>
                  <Field label="Objetivo del proyecto">
                    <textarea
                      className="min-h-[104px] w-full rounded-[18px] border border-border px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/15"
                      placeholder="Describe qué se espera obtener o lograr."
                      value={formState.objective}
                      onChange={(event) => setFormState((current) => ({ ...current, objective: event.target.value }))}
                    />
                  </Field>

                  <Field label="Variable principal">
                    <input
                      className="colmena-input w-full border border-border px-4"
                      placeholder="Ej. Satisfacción del cliente"
                      value={formState.mainVariable}
                      onChange={(event) => setFormState((current) => ({ ...current, mainVariable: event.target.value }))}
                    />
                  </Field>
                  <Field label="Variables secundarias">
                    <input
                      className="colmena-input w-full border border-border px-4"
                      placeholder="Ej. Calidad del servicio, tiempo de respuesta"
                      value={formState.secondaryVariables}
                      onChange={(event) =>
                        setFormState((current) => ({ ...current, secondaryVariables: event.target.value }))
                      }
                    />
                  </Field>

                  <Field label="Instrumentos referenciales">
                    <textarea
                      className="min-h-[104px] w-full rounded-[18px] border border-border px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/15"
                      placeholder="Ej. Cuestionario de satisfacción, escala Likert, encuesta..."
                      value={formState.instrumentReferences}
                      onChange={(event) =>
                        setFormState((current) => ({ ...current, instrumentReferences: event.target.value }))
                      }
                    />
                  </Field>
                  <div className="grid gap-5 md:grid-cols-2">
                    <Field label="Institución">
                      <input
                        className="colmena-input w-full border border-border px-4"
                        value={formState.institution}
                        onChange={(event) =>
                          setFormState((current) => ({ ...current, institution: event.target.value }))
                        }
                      />
                    </Field>
                    <Field label="Muestra planificada">
                      <input
                        className="colmena-input w-full border border-border px-4"
                        inputMode="numeric"
                        value={formState.sample_size_planned ?? ""}
                        onChange={(event) =>
                          setFormState((current) => ({
                            ...current,
                            sample_size_planned: event.target.value ? Number(event.target.value) : null,
                          }))
                        }
                      />
                    </Field>
                    <Field label="Población">
                      <input
                        className="colmena-input w-full border border-border px-4"
                        placeholder="Ej. Estudiantes de psicología de 5° ciclo"
                        value={formState.population_description}
                        onChange={(event) =>
                          setFormState((current) => ({ ...current, population_description: event.target.value }))
                        }
                      />
                    </Field>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 border-t border-border px-6 py-5">
            <button
              className="colmena-button-secondary"
              onClick={() => {
                setFormState(initialState);
                setIsOpen(false);
              }}
              type="button"
            >
              Cancelar
            </button>
            <PrimaryAction disabled={!formState.title.trim()} loading={isLoading} onClick={submit} type="button">
              Crear proyecto
            </PrimaryAction>
          </div>
        </>
      ) : null}
    </div>
  );
}
