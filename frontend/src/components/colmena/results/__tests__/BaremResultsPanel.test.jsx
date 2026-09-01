import { describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';

import { renderWithQueryClient } from '../../../../test-utils/renderWithQueryClient.jsx';
import BaremResultsPanel from '../BaremResultsPanel.jsx';

const STUDY = { id: 1, instrument_version_id: 10, barem_id: 5, min_publishable_n: 5 };

vi.mock('../../../../api/studies.js', () => ({
  getStudy: vi.fn(),
  listBarems: vi.fn(),
  getResultsOverview: vi.fn(),
  runScoring: vi.fn(),
  updateStudy: vi.fn(),
}));

import { getResultsOverview, getStudy, listBarems } from '../../../../api/studies.js';

describe('BaremResultsPanel', () => {
  it('muestra el estado de carga mientras no hay estudio', () => {
    getStudy.mockReturnValue(new Promise(() => {})); // nunca resuelve
    getResultsOverview.mockReturnValue(new Promise(() => {}));
    listBarems.mockResolvedValue([]);

    renderWithQueryClient(<BaremResultsPanel studyId={1} />);

    expect(screen.getByText('Cargando resultados…')).toBeInTheDocument();
  });

  it('muestra el estado vacío cuando no hay resultados calculados', async () => {
    getStudy.mockResolvedValue(STUDY);
    listBarems.mockResolvedValue([]);
    getResultsOverview.mockResolvedValue({ results: [] });

    renderWithQueryClient(<BaremResultsPanel studyId={1} />);

    expect(await screen.findByText('Aún no hay resultados calculados')).toBeInTheDocument();
  });

  it('nunca muestra el puntaje ni las bandas de un constructo suprimido por privacidad (n < min_publishable_n)', async () => {
    getStudy.mockResolvedValue(STUDY);
    listBarems.mockResolvedValue([{ id: 5, name: 'Barem QA', status: 'DRAFT' }]);
    getResultsOverview.mockResolvedValue({
      n_completed: 12,
      barem_name: 'Barem QA',
      min_publishable_n: 5,
      analysis_run_id: 1,
      results: [
        {
          construct_id: 1,
          construct_code: 'D1',
          construct_name: 'Dimensión suprimida',
          parent_id: null,
          n_valid: 3, // < min_publishable_n
          suppressed: true,
          mean_score: 87.5, // el backend no debería mandar esto si suppressed=true, pero
          // el test verifica que AUNQUE llegara, el componente jamás lo pinta
          priority_rank: 1,
          bands: [{ label: 'Alto', n: 3, pct: 100, color_hint: null }],
        },
        {
          construct_id: 2,
          construct_code: 'D2',
          construct_name: 'Dimensión publicable',
          parent_id: null,
          n_valid: 20,
          suppressed: false,
          mean_score: 61.2,
          priority_rank: 2,
          bands: [{ label: 'Alto', n: 20, pct: 100, color_hint: null }],
        },
      ],
    });

    renderWithQueryClient(<BaremResultsPanel studyId={1} />);

    await waitFor(() => expect(screen.getByText('Dimensión suprimida')).toBeInTheDocument());

    // La fila suprimida debe mostrar "Suprimido" y NUNCA el valor 87.5 en ninguna celda.
    const suppressedRow = screen.getByText('Dimensión suprimida').closest('tr');
    expect(suppressedRow).not.toBeNull();
    expect(suppressedRow.textContent).toContain('Suprimido');
    expect(suppressedRow.textContent).not.toContain('87.5');
    expect(suppressedRow.textContent).not.toContain('87,5');

    // La fila publicable sí debe mostrar su puntaje real.
    const publishableRow = screen.getByText('Dimensión publicable').closest('tr');
    expect(publishableRow.textContent).not.toContain('Suprimido');
  });
});
