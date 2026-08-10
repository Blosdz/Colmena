import type { NormalityTestResult } from "../api/reports";

/** Decisión de método de correlación que corresponde a un resultado de normalidad. */
export function normalityDecision(
  result: Pick<NormalityTestResult, "classification">,
): { text: string; tone: string } {
  if (result.classification === "normal") return { text: "Normal → Pearson", tone: "text-success" };
  if (result.classification === "non_normal") return { text: "No normal → Spearman", tone: "text-danger" };
  return { text: "No concluyente", tone: "text-muted" };
}
