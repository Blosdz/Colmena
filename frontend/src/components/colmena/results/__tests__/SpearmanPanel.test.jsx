import { describe, expect, it, vi } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { renderWithQueryClient } from '../../../../test-utils/renderWithQueryClient.jsx';
import { SegmentationPanel, SpearmanPanel } from '../SpearmanPanel.jsx';

vi.mock('../../../../api/analytics.js', () => ({
  runSpearmanMatrix: vi.fn(),
  compareConstructGroups: vi.fn(),
}));
vi.mock('../../../../api/variables.js', () => ({
  listExogenousFields: vi.fn(),
}));

import { compareConstructGroups, runSpearmanMatrix } from '../../../../api/analytics.js';
import { listExogenousFields } from '../../../../api/variables.js';

describe('SpearmanPanel — scatter binned (GAP-009: nunca pares crudos)', () => {
  it('nunca muestra "Sin pares graficables" cuando la celda seleccionada trae points_binned', async () => {
    listExogenousFields.mockResolvedValue([]);
    runSpearmanMatrix.mockResolvedValue({
      analysis_run_id: 1,
      study_id: 1,
      method: 'SPEARMAN',
      correction: 'BENJAMINI_HOCHBERG',
      normality_required: false,
      excluded: [],
      variables: [
        { key: 'x', source_type: 'CONSTRUCT', source_id: 1, code: 'D1', label: 'D1', measurement_level: 'SCALE' },
        { key: 'y', source_type: 'CONSTRUCT', source_id: 2, code: 'D5', label: 'D5', measurement_level: 'SCALE' },
      ],
      cells: [
        {
          x_key: 'x',
          y_key: 'y',
          rho: 0.42,
          p_value: 0.01,
          adjusted_p_value: 0.02,
          n: 120,
          magnitude: 'MODERADA',
          significant: true,
          points_binned: [
            { x_bin_center: 35, y_bin_center: 45, n: 12 },
            { x_bin_center: 55, y_bin_center: 65, n: 8 },
          ],
          warnings: [],
        },
      ],
    });

    renderWithQueryClient(<SpearmanPanel projectId={1} studyId={1} />);

    await userEvent.click(screen.getByRole('button', { name: 'Calcular matriz' }));

    await waitFor(() => expect(screen.getByText(/n = 120/)).toBeInTheDocument());
    expect(screen.queryByText('Sin pares graficables')).not.toBeInTheDocument();
  });

  it('muestra "Sin pares graficables" en vez de inventar puntos cuando no hay points_binned', async () => {
    listExogenousFields.mockResolvedValue([]);
    runSpearmanMatrix.mockResolvedValue({
      analysis_run_id: 1,
      study_id: 1,
      method: 'SPEARMAN',
      correction: 'BENJAMINI_HOCHBERG',
      normality_required: false,
      excluded: [],
      variables: [
        { key: 'x', source_type: 'CONSTRUCT', source_id: 1, code: 'D1', label: 'D1', measurement_level: 'SCALE' },
        { key: 'y', source_type: 'CONSTRUCT', source_id: 2, code: 'D5', label: 'D5', measurement_level: 'SCALE' },
      ],
      cells: [
        {
          x_key: 'x',
          y_key: 'y',
          rho: 0.42,
          p_value: 0.01,
          adjusted_p_value: 0.02,
          n: 120,
          magnitude: 'MODERADA',
          significant: true,
          points_binned: [],
          warnings: ['include_points no solicitado'],
        },
      ],
    });

    renderWithQueryClient(<SpearmanPanel projectId={1} studyId={1} />);

    await userEvent.click(screen.getByRole('button', { name: 'Calcular matriz' }));

    expect(await screen.findByText('Sin pares graficables')).toBeInTheDocument();
  });

  it('muestra el mensaje de error del backend cuando falla el cálculo de la matriz', async () => {
    listExogenousFields.mockResolvedValue([]);
    runSpearmanMatrix.mockRejectedValue(new Error('No se pudo calcular la matriz de correlación.'));

    renderWithQueryClient(<SpearmanPanel projectId={1} studyId={1} />);

    await userEvent.click(screen.getByRole('button', { name: 'Calcular matriz' }));

    expect(await screen.findByText('No se pudo calcular la matriz de correlación.')).toBeInTheDocument();
  });
});

describe('SegmentationPanel — supresión de privacidad n < 5', () => {
  it('nunca revela media/mediana de un grupo suprimido, ni en la tabla ni en el gráfico de barra', async () => {
    listExogenousFields.mockResolvedValue([
      { variable: { id: 9, name: 'Área', measurement_level: 'NOMINAL' }, question: { option_set_id: null } },
    ]);
    compareConstructGroups.mockResolvedValue({
      analysis_run_id: 1,
      study_id: 1,
      construct_id: 1,
      group_variable_id: 9,
      method: 'MANN_WHITNEY',
      statistic: 12.3,
      p_value: 0.03,
      effect_size: 0.4,
      effect_label: 'MODERADO',
      suppressed: false,
      groups: [
        { code: 'A', n: 3, suppressed: true, mean: null, median: null }, // n < 5 -> suprimido
        { code: 'B', n: 40, suppressed: false, mean: 55.4, median: 54.0 },
      ],
      warnings: ['Grupo A suprimido por tamaño mínimo (n < 5).'],
    });

    renderWithQueryClient(
      <SegmentationPanel
        projectId={1}
        studyId={1}
        versionId={undefined}
        overview={{ results: [{ construct_id: 1, construct_name: 'D1' }] }}
      />,
    );

    const [constructSelect, groupSelect] = screen.getAllByRole('combobox');
    await userEvent.selectOptions(constructSelect, '1');
    await userEvent.selectOptions(groupSelect, '9');
    fireEvent.click(screen.getByRole('button', { name: 'Comparar' }));

    // El grupo publicable (B, n=40) debe aparecer con su media real.
    await waitFor(() => expect(screen.getByText('B').closest('tr').textContent).toMatch(/55[.,]4/));

    // El grupo suprimido (A, n=3) nunca debe filtrar su media/mediana real, en ningún formato.
    const suppressedRow = screen.getByText('A').closest('tr');
    expect(suppressedRow.textContent).toContain('Suprimido');
    expect(suppressedRow.textContent).not.toMatch(/55[.,]4/);
    expect(suppressedRow.textContent).not.toMatch(/54[.,]0/);
  });
});
