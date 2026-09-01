/** Compartido entre PublicSurveyPage (modo "una pregunta a la vez") y
 * SurveyAllQuestionsView (modo "todas en pantalla") para decidir si una
 * respuesta cuenta como respondida (arrays vacíos y '' no cuentan). */
export function hasAnswerValue(value) {
  if (Array.isArray(value)) return value.length > 0;
  return value !== undefined && value !== null && value !== '';
}
