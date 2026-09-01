const LABELS = {
  ACTIVE: 'Activo', DRAFT: 'Borrador', ARCHIVED: 'Archivado', OPEN: 'Abierto', CLOSED: 'Cerrado',
  LOCKED: 'Congelado', PUBLISHED: 'Publicado', COMPLETED: 'Completado', FAILED: 'Fallido', PENDING: 'Pendiente',
  ACADEMIC: 'Académico', CENSO: 'CensoPÁS', CUSTOM: 'Personalizado', RESEARCH: 'Investigación',
  NOMINAL: 'Nominal', ORDINAL: 'Ordinal', SCALE: 'Escala', BINARY: 'Binaria',
  TEXT: 'Texto', INTEGER: 'Entero', DECIMAL: 'Decimal', CATEGORY: 'Categoría', BOOLEAN: 'Sí/No',
  DEMOGRAPHIC: 'Demográfica', EXOGENOUS: 'Exógena', DERIVED: 'Derivada', OUTCOME: 'Resultado',
  GROUPING: 'Agrupación', FILTER: 'Filtro', ANALYSIS: 'Análisis', REPORTING: 'Reporte',
  SCORED: 'Puntuable', CONTEXT: 'Contexto', EXCLUDED: 'Excluido', MEDIUM: 'Medio', SMALL: 'Pequeño', LARGE: 'Grande', NEGLIGIBLE: 'Despreciable',
  INDEPENDENT: 'Independiente', DEPENDENT: 'Dependiente', CONTROL: 'Control',
  INSTRUMENT: 'Instrumento', DATE: 'Fecha', DIRECT: 'Directa', REVERSE: 'Inversa',
  RIESGO_ALTO: 'Riesgo alto', RIESGO_MEDIO: 'Riesgo medio', FACTOR_PROTECTOR: 'Factor protector', REVISION: 'Revisión',
  OFFICIAL: 'Oficial', REFERENCE: 'Referencia', EXPLORATORY: 'Exploratorio',
  DIMENSION: 'Dimensión', SUBDIMENSION: 'Subdimensión', VARIABLE: 'Variable',
};

export function displayLabel(value, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  return LABELS[value] || String(value).replaceAll('_', ' ').toLocaleLowerCase('es').replace(/^./, (letter) => letter.toLocaleUpperCase('es'));
}
