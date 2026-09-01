import { useEffect, useMemo, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ShieldCheck } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { compareConstructGroups } from '../../../api/analytics.js';
import { Button } from '../../ui/Button.jsx';
import { Card } from '../../ui/Card.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';
import { formatNumber, formatPValue } from '../../../utils/format.js';
import { displayLabel } from '../../../utils/labels.js';

const METHOD_LABELS = {
  MANN_WHITNEY: 'Mann-Whitney U',
  KRUSKAL_WALLIS: 'Kruskal-Wallis',
  CHI_SQUARE: 'Chi-cuadrado',
};

function InferenceMetric({ label, value, title }) {
  return (
    <div className="rounded-xl border border-border p-3" title={title}>
      <p className="text-[11px] text-muted">{label}</p>
      <p className="mt-1 text-sm font-semibold text-dark">{value}</p>
    </div>
  );
}

export default function GroupComparisonsPanel({ studyId, overview, descriptives }) {
  const constructs = useMemo(
    () => (overview?.results || []).filter((item) => item.mean_score !== null),
    [overview],
  );
  const groupVariables = useMemo(() => {
    const seen = new Set();
    return (descriptives?.questions || []).filter((question) => {
      if (!question.variable_id || !['NOMINAL', 'ORDINAL', 'BINARY'].includes(question.measurement_level)) return false;
      if (seen.has(question.variable_id)) return false;
      seen.add(question.variable_id);
      return true;
    });
  }, [descriptives]);
  const [constructId, setConstructId] = useState('');
  const [groupVariableId, setGroupVariableId] = useState('');

  useEffect(() => {
    if (!constructId && constructs.length) setConstructId(String(constructs[0].construct_id));
  }, [constructId, constructs]);
  useEffect(() => {
    if (!groupVariableId && groupVariables.length) setGroupVariableId(String(groupVariables[0].variable_id));
  }, [groupVariableId, groupVariables]);

  const mutation = useMutation({
    mutationFn: () => compareConstructGroups(studyId, {
      construct_id: Number(constructId),
      group_variable_id: Number(groupVariableId),
    }),
  });

  const selectedVariable = groupVariables.find((item) => item.variable_id === Number(groupVariableId));
  const labels = new Map((selectedVariable?.frequencies || []).map((item) => [item.code, item.label]));
  const chartRows = (mutation.data?.groups || [])
    .filter((group) => !group.suppressed && group.mean !== null)
    .map((group) => ({ ...group, label: labels.get(group.code) || group.code }));

  if (!constructs.length || !groupVariables.length) {
    return (
      <Card>
        <EmptyState
          title="La comparación necesita un puntaje y una variable de perfil"
          description="Calcula al menos un constructo y vincula una variable nominal, ordinal o binaria como sexo, edad, área, contrato u horario."
        />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] lg:items-end">
          <label className="flex flex-col gap-2">
            <span className="colmena-label">Constructo</span>
            <select className="colmena-input" value={constructId} onChange={(event) => setConstructId(event.target.value)}>
              {constructs.map((item) => (
                <option key={item.construct_id} value={item.construct_id}>{item.construct_name}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-2">
            <span className="colmena-label">Comparar según</span>
            <select className="colmena-input" value={groupVariableId} onChange={(event) => setGroupVariableId(event.target.value)}>
              {groupVariables.map((item) => (
                <option key={item.variable_id} value={item.variable_id}>{item.variable_label || item.question_text}</option>
              ))}
            </select>
          </label>
          <Button
            disabled={!constructId || !groupVariableId}
            loading={mutation.isPending}
            onClick={() => mutation.mutate()}
            type="button"
          >
            Comparar grupos
          </Button>
        </div>
      </Card>

      {mutation.isError ? (
        <Card className="border-danger/20 bg-red-50/70 text-sm text-danger">
          {mutation.error?.message || 'No se pudo ejecutar la comparación.'}
        </Card>
      ) : null}

      {mutation.data ? (
        <>
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-dark">Descriptiva · Media por grupo</p>
                <p className="mt-1 text-xs text-muted">Las celdas pequeñas se ocultan según el mínimo publicable del estudio.</p>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-turquoiseSoft px-3 py-2 text-xs font-semibold text-turquoiseDark">
                <ShieldCheck size={15} />
                Umbral n ≥ {descriptives?.min_publishable_n}
              </div>
            </div>
            {chartRows.length ? (
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartRows}>
                    <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="mean" name="Media" fill="#F5B21A" radius={[7, 7, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="mt-4 rounded-xl border border-dashed border-border p-5 text-sm text-muted">
                No hay grupos publicables para graficar.
              </div>
            )}
          </Card>

          <Card padded={false}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-surfaceSoft">
                  <tr>
                    {['Grupo', 'n', 'Media', 'Mediana', 'Privacidad'].map((label) => (
                      <th key={label} className="px-4 py-3 text-xs font-semibold text-muted">{label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {mutation.data.groups.map((group) => (
                    <tr key={group.code} className="border-t border-border">
                      <td className="px-4 py-3 font-medium text-dark">{labels.get(group.code) || group.code}</td>
                      <td className="px-4 py-3">{group.n}</td>
                      <td className="px-4 py-3">{group.suppressed ? '—' : group.mean?.toFixed(2)}</td>
                      <td className="px-4 py-3">{group.suppressed ? '—' : group.median?.toFixed(2)}</td>
                      <td className="px-4 py-3 text-xs">
                        {group.suppressed ? <span className="font-semibold text-warning">Suprimido</span> : <span className="text-success">Publicable</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card>
            <p className="text-sm font-semibold text-dark">Inferencia · Resultado estadístico</p>
            <p className="mt-1 text-xs text-muted">
              La significancia (p) no equivale a importancia práctica: interpreta siempre junto al tamaño de efecto.
            </p>
            {mutation.data.suppressed ? (
              <div className="mt-3 rounded-xl border border-dashed border-border p-4 text-xs text-muted">
                Prueba suprimida: al menos un grupo está por debajo del mínimo publicable del estudio.
              </div>
            ) : mutation.data.method ? (
              <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-5">
                <InferenceMetric label="Método" value={METHOD_LABELS[mutation.data.method] || mutation.data.method} />
                <InferenceMetric label="Estadístico" value={formatNumber(mutation.data.statistic, { decimals: 2 })} />
                <InferenceMetric label="p" value={formatPValue(mutation.data.p_value)} />
                {mutation.data.adjusted_p_value !== undefined && mutation.data.adjusted_p_value !== null ? (
                  <InferenceMetric label="q (BH)" value={formatPValue(mutation.data.adjusted_p_value)} />
                ) : null}
                <InferenceMetric label="Tamaño de efecto" value={formatNumber(mutation.data.effect_size, { decimals: 2 })} />
                <InferenceMetric label="Magnitud" value={displayLabel(mutation.data.effect_label)} />
              </div>
            ) : (
              <div className="mt-3 rounded-xl border border-dashed border-border p-4 text-xs text-muted">
                No se pudo calcular una prueba estadística para esta comparación.
              </div>
            )}
          </Card>

          {mutation.data.warnings?.map((warning) => <p key={warning} className="text-xs text-warning">{warning}</p>)}
        </>
      ) : (
        <Card>
          <EmptyState title="Selecciona una comparación" description="Verás media y mediana sin exponer grupos por debajo del umbral de privacidad." />
        </Card>
      )}
    </div>
  );
}
