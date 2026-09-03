export type ExogenousOption = { label: string; value: number };

export type ParsedQuestion = {
  id: string;
  code: string;
  text: string;
  dimensionName: string;
  type: string;
  scale: string;
  reversed: boolean;
  required: boolean;
  scored: boolean;
  isImportance: boolean;
  status: "ready" | "missing_dimension" | "missing_scale" | "empty_text" | "review";
  /** "scale" = escala Likert compartida (por defecto); "exogenous" = respuesta propia del ítem (p. ej. Sexo). */
  responseKind?: "scale" | "exogenous";
  /** Solo si responseKind === "exogenous". */
  exogenousType?: "single_choice" | "number" | "text_short";
  exogenousOptions?: ExogenousOption[];
};

export function parseBulkQuestions(rawText: string): ParsedQuestion[] {
  const lines = rawText.split(/\r?\n/).filter(line => line.trim().length > 0);
  
  return lines.map((line, index) => {
    // Attempt to split by tab, fallback to pipe or semicolon
    let columns = line.split("\t");
    if (columns.length < 2 && line.includes("|")) {
      columns = line.split("|").map(c => c.trim());
    }

    let codeVal = `I${String(index + 1).padStart(2, "0")}`;
    let textVal = columns[0] || "";
    let dimensionName = columns[2] || "";
    let type = columns[3] || "Likert";
    let scale = columns[4] || "";
    let reversedRaw = columns[5] || "No";
    let requiredRaw = columns[6] || "Sí";

    if (columns.length >= 2) {
      codeVal = columns[0].trim();
      textVal = columns[1].trim();
    } else {
      // Fallback for pasted sentences like "10. Me siento seguro..."
      const match = textVal.match(/^(\d+[\.\-]?)\s+(.*)$/);
      if (match) {
        codeVal = match[1].trim();
        textVal = match[2].trim();
      }
    }

    const reversed = reversedRaw.toLowerCase().includes("si") || reversedRaw.toLowerCase().includes("yes");
    const required = requiredRaw.toLowerCase().includes("si") || requiredRaw.toLowerCase().includes("yes");
    
    let status: ParsedQuestion["status"] = "ready";
    if (!textVal) status = "empty_text";
    else if (!dimensionName) status = "missing_dimension";
    else if (!scale) status = "missing_scale";

    return {
      id: Date.now().toString() + index,
      code: codeVal,
      text: textVal,
      dimensionName,
      type,
      scale,
      reversed,
      required,
      scored: true, // by default true for Likert
      isImportance: false,
      status
    };
  });
}
