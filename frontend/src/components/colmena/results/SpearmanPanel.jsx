import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts';

import { compareConstructGroups, runSpearmanMatrix } from '../../../api/analytics.js';
import { listExogenousFields } from '../../../api/variables.js';
import { useOptionLabels } from '../../../hooks/useOptionLabels.js';
import { formatNumber, formatPValue } from '../../../utils/format.js';
import { displayLabel } from '../../../utils/labels.js';
import { Button } from '../../ui/Button.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';
import { Table, TableContainer, Td, THead, Th, Tr } from '../../ui/Table.jsx';

const MAGNITUDE_HINT =
  'Escala de interpretación de |ρ|: < 0,10 despreciable · 0,10–0,29 débil · 0,30–0,49 moderada · ≥ 0,50 fuerte.';

export function SpearmanPanel({ projectId, studyId }) {
  const [exogenousIds, setExogenousIds] = useState([]);
  const [cellIndex, setCellIndex] = useState(0);
  const [view, setView] = useState('matrix');
  const { data: fields = [] } = useQuery({
    queryKey: ['exogenousFields', projectId],
    queryFn: () => listExogenousFields(projectId),
  });
  const rankable = fields.filter(({ variable }) => ['ORDINAL', 'SCALE', 'BINARY'].includes(variable.measurement_level));

  const mutation = useMutation({
    mutationFn: () =>
      runSpearmanMatrix(studyId, { exogenous_variable_ids: exogenousIds, include_points: true }),
    onSuccess: () => setCellIndex(0),
    meta: { skipGlobalToast: true },
  });

  const selectedCell = mutation.data?.cells?.[cellIndex];
  const byKey = useMemo(
    () => Object.fromEntries((mutation.data?.variables || []).map((item) => [item.key, item])),
    [mutation.data],
  );
  const toggle = (id) =>
    setExogenousIds((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));

  return (
    <div className="colmena-panel">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-dark">Matriz de Spearman</p>
          <p className="mt-1 text-xs text-muted">
            Incluye todos los constructos y, opcionalmente, variables exógenas ordenables.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {mutation.data ? (
            <div className="flex rounded-lg bg-surfaceSoft p-0.5">
              <button type="button" className={`colmena-pill-tab ${view === 'matrix' ? 'active' : ''}`} onClick={() => setView('matrix')}>Matriz</button>
              <button type="button" className={`colmena-pill-tab ${view === 'list' ? 'active' : ''}`} onClick={() => setView('list')}>Lista</button>
            </div>
          ) : null}
          <Button variant="primary" size="sm" onClick={() => mutation.mutate()} loading={mutation.isPending}>Calcular matriz</Button>
        </div>
      </div>

      {rankable.length ? (
        <div>
          <p className="colmena-label mb-2">Variables exógenas a incluir</p>
          <div className="flex flex-wrap gap-2">
            {rankable.map(({ variable }) => (
              <button
                key={variable.id}
                type="button"
                onClick={() => toggle(variable.id)}
                className={`colmena-badge cursor-pointer ${
                  exogenousIds.includes(variable.id) ? 'bg-amber text-white' : 'bg-amber/10 text-yellowDark'
                }`}
              >
                {variable.name}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {mutation.isError ? <p className="text-sm text-danger">{mutation.error?.message}</p> : null}

      {!mutation.data ? (
        <EmptyState
          title="Correlaciones de constructos"
          description="El backend usa Spearman aunque la normalidad no se cumpla y ajusta los p-valores por Benjamini–Hochberg."
        />
      ) : (
        <>
          <div className="rounded-xl bg-surfaceSoft px-3 py-2 text-xs text-muted">
            Método: Spearman · Corrección: Benjamini–Hochberg · Normalidad requerida: no. Una correlación no
            demuestra causalidad.
          </div>
          {mutation.data.excluded.map((message) => (
            <p key={message} className="text-xs text-danger">
              {message}
            </p>
          ))}

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.6fr)]">
            {view === 'matrix' ? (
              <SpearmanMatrix variables={mutation.data.variables} cells={mutation.data.cells} selectedIndex={cellIndex} onSelect={setCellIndex} />
            ) : (
            <TableContainer>
              <Table>
                <THead>
                  <Tr>
                    <Th>Variables</Th>
                    <Th align="right">ρ</Th>
                    <Th align="right">p ajustado</Th>
                    <Th align="right">n</Th>
                    <Th title={MAGNITUDE_HINT}>Magnitud</Th>
                  </Tr>
                </THead>
                <tbody>
                  {mutation.data.cells.map((cell, index) => (
                    <Tr
                      key={`${cell.x_key}-${cell.y_key}`}
                      onClick={() => setCellIndex(index)}
                      className={`cursor-pointer ${cellIndex === index ? 'bg-amber/10' : 'hover:bg-surfaceSoft'}`}
                    >
                      <Td>
                        {byKey[cell.x_key]?.label} × {byKey[cell.y_key]?.label}
                      </Td>
                      <Td align="right" className="font-semibold">
                        {formatNumber(cell.rho, { decimals: 2 })}
                      </Td>
                      <Td align="right">
                        {formatPValue(cell.adjusted_p_value)} {cell.significant ? '•' : ''}
                      </Td>
                      <Td align="right">{cell.n}</Td>
                      <Td title={MAGNITUDE_HINT}>{cell.magnitude || '—'}</Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
            </TableContainer>
            )}

            <div className="flex h-[360px] flex-col rounded-2xl border border-border p-4">
              <p className="text-sm font-semibold text-dark">
                {selectedCell ? `${byKey[selectedCell.x_key]?.label} × ${byKey[selectedCell.y_key]?.label}` : 'Dispersión'}
              </p>
              {selectedCell ? (
                <p className="mt-0.5 text-xs text-muted">
                  n = {selectedCell.n} · ρ = {formatNumber(selectedCell.rho, { decimals: 2 })} ·{' '}
                  {formatPValue(selectedCell.adjusted_p_value)}
                </p>
              ) : null}
              {selectedCell?.points_binned?.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      type="number"
                      dataKey="x_bin_center"
                      name={byKey[selectedCell.x_key]?.label}
                      label={{ value: byKey[selectedCell.x_key]?.label, position: 'insideBottom', offset: -4, fontSize: 11 }}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="y_bin_center"
                      name={byKey[selectedCell.y_key]?.label}
                      label={{ value: byKey[selectedCell.y_key]?.label, angle: -90, position: 'insideLeft', fontSize: 11 }}
                      tick={{ fontSize: 11 }}
                    />
                    {/* El tamaño del punto representa cuántos pares cayeron en ese bin
                        (agregación de privacidad E-09: nunca coordenadas individuales). */}
                    <ZAxis type="number" dataKey="n" range={[40, 260]} name="pares" />
                    <Tooltip
                      cursor={{ strokeDasharray: '3 3' }}
                      formatter={(value, name) => (name === 'pares' ? [value, 'pares en el bin'] : [formatNumber(value, { decimals: 2 }), name])}
                    />
                    <Scatter data={selectedCell.points_binned} fill="#F5B21A" fillOpacity={0.75} />
                  </ScatterChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex flex-1 items-center justify-center">
                  <EmptyState title="Sin pares graficables" description={selectedCell?.warnings?.join(' ') || 'Selecciona una fila.'} />
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function SegmentationPanel({ projectId, studyId, versionId, overview }) {
  const [constructId, setConstructId] = useState('');
  const [variableId, setVariableId] = useState('');
  const { data: fields = [] } = useQuery({
    queryKey: ['exogenousFields', projectId],
    queryFn: () => listExogenousFields(projectId),
  });
  const grouping = fields.filter(({ variable }) => ['NOMINAL', 'ORDINAL', 'BINARY'].includes(variable.measurement_level));
  const selectedField = grouping.find(({ variable }) => String(variable.id) === variableId);
  const { resolveLabel } = useOptionLabels(versionId);

  const mutation = useMutation({
    mutationFn: () =>
      compareConstructGroups(studyId, { construct_id: Number(constructId), group_variable_id: Number(variableId) }),
    meta: { skipGlobalToast: true },
  });

  const maxAbsMean = Math.max(1, ...(mutation.data?.groups || []).map((g) => Math.abs(g.mean ?? 0)));

  return (
    <div className="colmena-panel">
      <div>
        <p className="text-sm font-semibold text-dark">Segmentación por datos exógenos</p>
        <p className="mt-1 text-xs text-muted">
          Compara puntajes de un constructo entre sexo, sede, rango de edad u otros perfiles. No altera el scoring.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
        <label className="flex flex-col gap-2">
          <span className="colmena-label">Constructo</span>
          <select className="colmena-input h-10 px-3 text-sm" value={constructId} onChange={(event) => setConstructId(event.target.value)}>
            <option value="">Selecciona…</option>
            {(overview?.results || []).map((item) => (
              <option key={item.construct_id} value={item.construct_id}>
                {item.construct_name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-2">
          <span className="colmena-label">Variable de grupo</span>
          <select className="colmena-input h-10 px-3 text-sm" value={variableId} onChange={(event) => setVariableId(event.target.value)}>
            <option value="">Selecciona…</option>
            {grouping.map(({ variable }) => (
              <option key={variable.id} value={variable.id}>
                {variable.name}
              </option>
            ))}
          </select>
        </label>
        <Button
          variant="primary"
          size="sm"
          onClick={() => mutation.mutate()}
          loading={mutation.isPending}
          disabled={!constructId || !variableId}
        >
          Comparar
        </Button>
      </div>

      {mutation.isError ? <p className="text-sm text-danger">{mutation.error?.message}</p> : null}

      {mutation.data ? (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <Metric label="Método" value={mutation.data.method || 'Suprimido'} />
            <Metric label="Estadístico" value={formatNumber(mutation.data.statistic, { decimals: 2 })} />
            <Metric label="p" value={formatPValue(mutation.data.p_value)} />
            <Metric label="Efecto" value={formatNumber(mutation.data.effect_size, { decimals: 2 })} />
            <Metric label="Magnitud" value={displayLabel(mutation.data.effect_label)} title={MAGNITUDE_HINT} />
          </div>

          <TableContainer>
            <Table>
              <THead>
                <Tr>
                  <Th>Grupo</Th>
                  <Th align="right">n</Th>
                  <Th align="right">Media</Th>
                  <Th align="right">Mediana</Th>
                  <Th className="w-40">Distribución</Th>
                </Tr>
              </THead>
              <tbody>
                {mutation.data.groups.map((group) => (
                  <Tr key={group.code}>
                    <Td className="font-medium">
                      {selectedField ? resolveLabel(selectedField.question.option_set_id, group.code) : group.code}
                    </Td>
                    <Td align="right">{group.n}</Td>
                    <Td align="right">{group.suppressed ? 'Suprimido' : formatNumber(group.mean, { decimals: 2 })}</Td>
                    <Td align="right">{group.suppressed ? 'Suprimido' : formatNumber(group.median, { decimals: 2 })}</Td>
                    <Td>
                      {group.suppressed || group.mean == null ? null : (
                        <div className="h-2 w-full overflow-hidden rounded-full bg-surfaceSoft">
                          <div
                            className="h-full rounded-full bg-amber"
                            style={{ width: `${Math.max(4, (Math.abs(group.mean) / maxAbsMean) * 100)}%` }}
                          />
                        </div>
                      )}
                    </Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </TableContainer>

          {mutation.data.warnings.map((warning) => (
            <p key={warning} className="text-xs text-danger">
              {warning}
            </p>
          ))}
        </>
      ) : (
        <EmptyState
          title="Elige un constructo y un grupo"
          description="Las celdas pequeñas se suprimen en el backend según el mínimo publicable del estudio."
        />
      )}
    </div>
  );
}

export function SpearmanMatrix({ variables = [], cells = [], selectedIndex, onSelect }) {
  const indexByPair = useMemo(() => {
    const entries = new Map();
    cells.forEach((cell, index) => {
      entries.set(`${cell.x_key}|${cell.y_key}`, { cell, index });
      entries.set(`${cell.y_key}|${cell.x_key}`, { cell, index });
    });
    return entries;
  }, [cells]);

  return (
    <div className="overflow-auto rounded-2xl border border-border">
      <table className="min-w-full border-collapse text-xs">
        <thead className="sticky top-0 z-[1] bg-surfaceSoft">
          <tr>
            <th className="sticky left-0 z-[2] min-w-36 border-b border-r border-border bg-surfaceSoft px-3 py-2 text-left text-muted">Variable</th>
            {variables.map((variable) => (
              <th key={variable.key} className="min-w-20 border-b border-border px-2 py-2 text-center font-semibold text-muted" title={variable.label}>
                {variable.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {variables.map((row, rowIndex) => (
            <tr key={row.key}>
              <th className="sticky left-0 z-[1] border-b border-r border-border bg-white px-3 py-2 text-left font-medium text-dark">{row.label}</th>
              {variables.map((column, columnIndex) => {
                if (rowIndex === columnIndex) return <td key={column.key} className="border-b border-border bg-surfaceSoft text-center font-semibold">1</td>;
                const match = indexByPair.get(`${row.key}|${column.key}`);
                const rho = match?.cell?.rho;
                const alpha = rho == null ? 0 : 0.12 + Math.abs(rho) * 0.7;
                const background = rho == null ? 'transparent' : rho >= 0 ? `rgba(21,128,61,${alpha})` : `rgba(220,38,38,${alpha})`;
                return (
                  <td key={column.key} className="border-b border-border p-1 text-center">
                    {match ? (
                      <button
                        type="button"
                        onClick={() => onSelect(match.index)}
                        className={`h-9 w-full rounded-md font-semibold ${match.index === selectedIndex ? 'ring-2 ring-dark ring-offset-1' : ''}`}
                        style={{ background, color: Math.abs(rho) >= 0.45 ? '#fff' : '#1c1f24' }}
                        title={`${row.label} × ${column.label}: ρ ${formatNumber(rho, { decimals: 2 })}`}
                      >
                        {formatNumber(rho, { decimals: 2 })}
                      </button>
                    ) : '—'}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center justify-end gap-3 border-t border-border px-3 py-2 text-[11px] text-muted">
        <span className="h-2.5 w-8 rounded bg-danger/70" /> −1
        <span className="h-2.5 w-8 rounded bg-surfaceSoft" /> 0
        <span className="h-2.5 w-8 rounded bg-success/70" /> +1
      </div>
    </div>
  );
}

function Metric({ label, value, title }) {
  return (
    <div className="rounded-xl border border-border p-4" title={title}>
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 font-semibold text-dark">{value}</p>
    </div>
  );
}
