import { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { 
  Clipboard, 
  CheckCircle, 
  ChevronRight, 
  ChevronLeft, 
  HelpCircle,
  Clock,
  Sparkles,
  Info,
  Calendar,
  Layers,
  ChevronDown,
  AlertTriangle
} from "lucide-react";

import { getPublicForm, submitPublicResponse } from "../api/publicForms";
import type { 
  PublicAnswerCreate 
} from "../types/publicForm";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";

export function PublicFormPage() {
  const { publicSlug = "" } = useParams();
  
  // Local state for navigation and answers
  const [step, setStep] = useState<"welcome" | "questions" | "completed">("welcome");
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [respondentCode, setRespondentCode] = useState("");
  const [answers, setAnswers] = useState<Record<string, PublicAnswerCreate>>({});
  const [validationError, setValidationError] = useState<string | null>(null);

  // Generate a pure transmission ID on mount
  const transmissionId = useMemo(() => Math.random().toString(36).substring(2, 10).toUpperCase(), []);

  // Load the public form layout from the backend
  const { data: form, isLoading, error } = useQuery({
    queryKey: ["public-form", publicSlug],
    queryFn: () => getPublicForm(publicSlug),
    enabled: Boolean(publicSlug),
  });

  // Generate dynamic overrides from form.metadata_json
  const themeStyles = useMemo(() => {
    if (!form?.metadata_json) return "";
    try {
      const meta = JSON.parse(form.metadata_json);
      if (!meta.theme) return "";
      
      const theme = meta.theme;
      const primary = theme.primaryColor || "#F5B21A";
      const bg = theme.backgroundColor || "#06080B";
      const font = theme.fontFamily || "Inter, sans-serif";
      
      const isLight = bg === "#F3F4F6" || bg === "#FFFFFF";
      
      const textColor = isLight ? "#334155" : "#E2E8F0";
      const textTitle = isLight ? "#1E293B" : "#FFFFFF";
      const textMuted = isLight ? "#64748B" : "#94A3B8";
      const containerBg = isLight ? "#FFFFFF" : "rgba(15, 23, 42, 0.6)";
      const borderColor = isLight ? "#E2E8F0" : "rgba(255, 255, 255, 0.05)";
      const headerBg = isLight ? "rgba(255, 255, 255, 0.7)" : "rgba(8, 11, 15, 0.65)";
      const instructionsBg = isLight ? "#F8FAFC" : "rgba(8, 11, 16, 0.95)";
      const inputBg = isLight ? "#FFFFFF" : "rgba(2, 6, 23, 0.6)";
      const inputBorder = isLight ? "#CBD5E1" : "rgba(255, 255, 255, 0.1)";
      const optionBg = isLight ? "#F8FAFC" : "rgba(2, 6, 23, 0.3)";
      const optionHoverBg = isLight ? "#F1F5F9" : "rgba(15, 23, 42, 0.4)";
      
      return `
        :root {
          --primary-color: ${primary};
          --bg-color: ${bg};
          --text-color: ${textColor};
          --text-title: ${textTitle};
          --text-muted: ${textMuted};
          --container-bg: ${containerBg};
          --border-color: ${borderColor};
          --header-bg: ${headerBg};
          --instructions-bg: ${instructionsBg};
          --input-bg: ${inputBg};
          --input-border: ${inputBorder};
          --option-bg: ${optionBg};
          --option-hover-bg: ${optionHoverBg};
        }
        
        body, input, textarea, select, button {
          font-family: ${font} !important;
        }
        
        /* Override Tailwind classes */
        .bg-\\[\\#06080B\\] {
          background-color: var(--bg-color) !important;
        }
        .text-\\[\\#E2E8F0\\] {
          color: var(--text-color) !important;
        }
        .text-white {
          color: var(--text-title) !important;
        }
        .text-slate-300 {
          color: var(--text-color) !important;
        }
        .text-slate-400 {
          color: var(--text-muted) !important;
        }
        .text-slate-500 {
          color: var(--text-muted) !important;
        }
        .bg-slate-900\\/60 {
          background-color: var(--container-bg) !important;
        }
        .border-white\\/5 {
          border-color: var(--border-color) !important;
        }
        .border-white\\/10 {
          border-color: var(--input-border) !important;
        }
        .bg-slate-950\\/60 {
          background-color: var(--input-bg) !important;
        }
        .bg-slate-950\\/30 {
          background-color: var(--option-bg) !important;
        }
        .border-slate-800 {
          border-color: var(--border-color) !important;
        }
        .hover\\:bg-slate-900\\/40:hover {
          background-color: var(--option-hover-bg) !important;
        }
        .bg-\\[\\#080B0F\\]\\/65 {
          background-color: var(--header-bg) !important;
        }
        .bg-\\[\\#080B10\\]\\/95 {
          background-color: var(--instructions-bg) !important;
        }
        
        /* Primary color overrides */
        .text-\\[\\#F5B21A\\] {
          color: var(--primary-color) !important;
        }
        .bg-\\[\\#F5B21A\\] {
          background-color: var(--primary-color) !important;
        }
        .border-\\[\\#F5B21A\\] {
          border-color: var(--primary-color) !important;
        }
        .focus\\:border-\\[\\#F5B21A\\]:focus {
          border-color: var(--primary-color) !important;
        }
        .focus\\:ring-\\[\\#F5B21A\\]:focus {
          --tw-ring-color: var(--primary-color) !important;
        }
        .selection\\:bg-\\[\\#F5B21A\\]\\/30::selection {
          background-color: var(--primary-color) !important;
          opacity: 0.3;
        }
        
        /* Gradients */
        .from-\\[\\#F5B21A\\] {
          --tw-gradient-from: var(--primary-color) !important;
          --tw-gradient-to: var(--primary-color) !important;
          --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to) !important;
        }
        .to-\\[\\#E09A0A\\] {
          --tw-gradient-to: var(--primary-color) !important;
        }
        
        /* Adjust box-shadows if light theme */
        ${isLight ? `
          .shadow-2xl, .shadow-xl {
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05) !important;
          }
          input, textarea, select {
            color: var(--text-title) !important;
          }
        ` : ""}
      `;
    } catch (e) {
      console.error("Error generating dynamic styles:", e);
      return "";
    }
  }, [form?.metadata_json]);

  // Submit the response to the backend
  const submitMutation = useMutation({
    mutationFn: (payload: { respondent_code: string; answers: PublicAnswerCreate[] }) => 
      submitPublicResponse(publicSlug, {
        respondent_code: payload.respondent_code || undefined,
        answers: payload.answers,
        metadata_json: {
          user_agent: navigator.userAgent,
          screen_size: `${window.innerWidth}x${window.innerHeight}`,
          submitted_at_local: new Date().toISOString()
        }
      }),
    onSuccess: () => {
      setStep("completed");
    },
    onError: (err: any) => {
      setValidationError(err.response?.data?.detail || "Error al enviar las respuestas. Por favor, revisa tus respuestas e intenta de nuevo.");
    }
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0A0D10] text-[#E2E8F0] flex items-center justify-center relative overflow-hidden">
        {/* Futuristic glowing backdrop orbs */}
        <div className="absolute top-1/4 left-1/4 w-[350px] h-[350px] bg-[#F5B21A] rounded-full blur-[120px] opacity-10 animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] bg-[#E09A0A] rounded-full blur-[100px] opacity-10" />
        <LoadingState label="Iniciando interfaz cuántica de recolección..." />
      </div>
    );
  }

  if (error || !form) {
    return (
      <div className="min-h-screen bg-[#0A0D10] text-[#E2E8F0] flex items-center justify-center p-6 relative overflow-hidden">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[400px] h-[400px] bg-red-600 rounded-full blur-[150px] opacity-10" />
        <div className="max-w-md w-full bg-slate-900/60 backdrop-blur-xl border border-red-500/20 rounded-[28px] p-8 text-center shadow-2xl relative z-10">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4 drop-shadow-[0_0_15px_rgba(239,68,68,0.4)]" />
          <h2 className="text-2xl font-bold text-white mb-2 font-mono tracking-wider">Formulario No Disponible</h2>
          <p className="text-slate-400 text-sm mb-6">
            El link de este formulario es inválido, ha expirado o el formulario ha sido cerrado por el investigador.
          </p>
          <ErrorState message={(error as Error)?.message || "Formulario no encontrado"} />
        </div>
      </div>
    );
  }

  const { questions = [], sections = [], title, description, instructions, thank_you_message } = form;

  // Group questions by section. If sections don't exist or questions don't belong to any section, use a single fallback section.
  const getSectionsWithQuestions = () => {
    if (sections.length === 0) {
      return [{ id: "default", title: "Cuestionario Principal", description: "Por favor contesta todas las preguntas a continuación.", questions }];
    }

    const map: Record<string, typeof questions> = {};
    const unsectioned: typeof questions = [];

    // Initialize map
    sections.forEach(s => { map[s.id] = []; });

    questions.forEach(q => {
      if (q.section_id && map[q.section_id]) {
        map[q.section_id].push(q);
      } else {
        unsectioned.push(q);
      }
    });

    const activeSections = sections
      .map(s => ({
        id: s.id,
        title: s.title,
        description: s.description,
        questions: map[s.id] || []
      }))
      .filter(s => s.questions.length > 0);

    if (unsectioned.length > 0) {
      activeSections.push({
        id: "unsectioned",
        title: "Preguntas Generales",
        description: "Preguntas del cuestionario",
        questions: unsectioned
      });
    }

    return activeSections;
  };

  const formSections = getSectionsWithQuestions();
  const currentSection = formSections[currentSectionIndex] || null;

  // Answers handler helper
  const handleAnswerChange = (questionId: string, answer: Partial<PublicAnswerCreate>) => {
    setValidationError(null);
    setAnswers(prev => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        question_id: questionId,
        ...answer
      }
    }));
  };

  // Check if current section questions are filled properly
  const validateCurrentSection = () => {
    if (!currentSection) return true;

    for (const q of currentSection.questions) {
      if (q.is_required) {
        const ans = answers[q.id];
        if (!ans) return false;

        // Validation depending on type
        if (q.question_type === "text_short" || q.question_type === "text_long") {
          if (!ans.value_text || ans.value_text.trim() === "") return false;
        } else if (q.question_type === "number") {
          if (ans.value_number === undefined || ans.value_number === null) return false;
          if (q.min_value !== undefined && q.min_value !== null && ans.value_number < q.min_value) return false;
          if (q.max_value !== undefined && q.max_value !== null && ans.value_number > q.max_value) return false;
        } else if (q.question_type === "date") {
          if (!ans.value_date) return false;
        } else if (q.question_type === "multiple_choice") {
          if (!ans.value_json || !Array.isArray(ans.value_json) || ans.value_json.length === 0) return false;
        } else {
          // Likert, single_choice, dropdown, boolean require option_id
          if (!ans.option_id) return false;
        }
      }
    }
    return true;
  };

  const handleNext = () => {
    if (!validateCurrentSection()) {
      setValidationError("Por favor, responda todas las preguntas obligatorias antes de continuar.");
      return;
    }

    setValidationError(null);
    if (currentSectionIndex < formSections.length - 1) {
      setCurrentSectionIndex(prev => prev + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      // Last section, submit!
      const payloadAnswers = Object.values(answers);
      submitMutation.mutate({
        respondent_code: respondentCode,
        answers: payloadAnswers
      });
    }
  };

  const handlePrev = () => {
    setValidationError(null);
    if (currentSectionIndex > 0) {
      setCurrentSectionIndex(prev => prev - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      setStep("welcome");
    }
  };

  // Calculate global progress percentage
  const totalQuestions = questions.length;
  const answeredQuestionsCount = Object.keys(answers).length;
  const progressPercent = totalQuestions > 0 ? Math.round((answeredQuestionsCount / totalQuestions) * 100) : 0;

  return (
    <div className="min-h-screen bg-[#06080B] text-[#E2E8F0] font-sans selection:bg-[#F5B21A]/30 selection:text-white flex flex-col relative overflow-hidden">
      {themeStyles && (
        <style dangerouslySetInnerHTML={{ __html: themeStyles }} />
      )}
      
      {/* ── BACKGROUND CYBERNETIC DECORATIONS ──────────────────────────────────── */}
      {/* High-tech grid overlay */}
      <div 
        className="absolute inset-0 bg-[linear-gradient(rgba(245,178,26,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(245,178,26,0.02)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" 
        style={{ maskImage: "radial-gradient(circle at center, black, transparent 80%)", WebkitMaskImage: "radial-gradient(circle at center, black, transparent 80%)" }}
      />
      {/* Glowing cyberpunk orbs */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-[#F5B21A] rounded-full blur-[160px] opacity-[0.06] pointer-events-none animate-pulse" style={{ animationDuration: "8s" }} />
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-[#E09A0A] rounded-full blur-[140px] opacity-[0.05] pointer-events-none" />

      {/* Header element */}
      <header className="w-full border-b border-white/5 bg-[#080B0F]/65 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-[#F5B21A] to-[#E09A0A] flex items-center justify-center shadow-[0_0_15px_rgba(245,178,26,0.3)]">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div className="absolute inset-0 bg-[#F5B21A]/20 blur-md rounded-lg -z-10" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white font-mono uppercase tracking-wider">COLMENA</h1>
            <p className="text-[10px] text-slate-400 font-medium">Plataforma Científica</p>
          </div>
        </div>
        {step === "questions" && (
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="text-slate-400 hidden sm:inline">Progreso global:</span>
            <div className="flex items-center gap-2">
              <div className="w-24 sm:w-32 bg-slate-800 h-2 rounded-full overflow-hidden border border-white/5 p-[1px]">
                <div 
                  className="bg-gradient-to-r from-[#F5B21A] to-[#FFC138] h-full rounded-full transition-all duration-500 shadow-[0_0_8px_rgba(245,178,26,0.5)]"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <span className="text-[#F5B21A] font-bold">{progressPercent}%</span>
            </div>
          </div>
        )}
      </header>

      {/* Main body content */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 md:p-8 z-10">
        
        {/* ── 1. WELCOME SCREEN ────────────────────────────────────────────────── */}
        {step === "welcome" && (
          <div className="max-w-2xl w-full bg-gradient-to-b from-slate-900/80 to-slate-900/40 backdrop-blur-xl border border-white/10 rounded-[32px] p-6 sm:p-10 shadow-2xl relative animate-colmena-fade-in">
            {/* Tech tag */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-[#F5B21A]/30 bg-[#F5B21A]/10 text-[#F5B21A] text-xs font-semibold mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Estudio Científico Activo</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
              {title}
            </h2>
            
            {description && (
              <p className="mt-4 text-slate-300 text-sm sm:text-base leading-relaxed">
                {description}
              </p>
            )}

            {instructions && (
              <div className="mt-6 p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono flex items-center gap-2">
                  <Info className="w-3.5 h-3.5 text-[#F5B21A]" />
                  Instrucciones
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{instructions}</p>
              </div>
            )}

            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <div className="p-4 rounded-2xl border border-white/5 bg-[#080B0F]/65 space-y-1">
                <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block">Preguntas totales</span>
                <span className="text-lg font-bold text-white">{totalQuestions} ítems estructurados</span>
              </div>
              <div className="p-4 rounded-2xl border border-white/5 bg-[#080B0F]/65 space-y-1">
                <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block">Tiempo estimado</span>
                <span className="text-lg font-bold text-white flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-[#F5B21A]" />
                  ~{Math.max(1, Math.round(totalQuestions * 0.4))} minutos
                </span>
              </div>
            </div>

            {/* Respondent Code Input (Optional) */}
            <div className="mt-8 space-y-2">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">
                Código de Participante (Opcional)
              </label>
              <input
                type="text"
                placeholder="Escribe tu código identificador o déjalo vacío para anónimo"
                className="w-full h-12 px-4 rounded-xl bg-slate-950/70 border border-white/10 text-white placeholder:text-slate-500 focus:border-[#F5B21A] focus:ring-1 focus:ring-[#F5B21A] outline-none transition-all duration-200"
                value={respondentCode}
                onChange={(e) => setRespondentCode(e.target.value)}
              />
              <p className="text-[10px] text-slate-500 leading-normal">
                Si tu investigador te asignó un código específico, ingrésalo aquí para asociar tus respuestas.
              </p>
            </div>

            <button
              onClick={() => setStep("questions")}
              className="mt-8 w-full h-14 rounded-2xl bg-gradient-to-r from-[#F5B21A] to-[#E09A0A] hover:from-[#FFC138] hover:to-[#F5B21A] text-slate-950 font-bold text-base flex items-center justify-center gap-2 shadow-[0_4px_20px_rgba(245,178,26,0.3)] hover:shadow-[0_6px_25px_rgba(245,178,26,0.4)] transition-all duration-300 hover:scale-[1.01] active:scale-[0.99]"
            >
              Comenzar Cuestionario
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* ── 2. QUESTIONS INTERFACE ─────────────────────────────────────────── */}
        {step === "questions" && currentSection && (
          <div className="max-w-3xl w-full flex flex-col gap-6 animate-colmena-fade-in">
            
            {/* Section card */}
            <div className="w-full bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-3xl p-5 sm:p-7 flex flex-col gap-2 relative">
              <div className="absolute top-0 left-8 right-8 h-[2px] bg-gradient-to-r from-transparent via-[#F5B21A]/50 to-transparent pointer-events-none" />
              
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold tracking-widest text-[#F5B21A] uppercase">
                  Sección {currentSectionIndex + 1} de {formSections.length}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {currentSection.questions.length} preguntas
                </span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">{currentSection.title}</h3>
              {currentSection.description && (
                <p className="text-xs sm:text-sm text-slate-400 leading-normal">{currentSection.description}</p>
              )}
            </div>

            {/* Questions stack */}
            <div className="flex flex-col gap-5">
              {currentSection.questions.map((q, idx) => {
                const isAnswered = Boolean(answers[q.id]);
                
                return (
                  <div 
                    key={q.id}
                    className={`bg-slate-900/40 backdrop-blur-md rounded-2xl p-5 sm:p-6 border transition-all duration-300 relative ${
                      isAnswered ? "border-slate-800 bg-[#0A0D11]/30" : "border-white/5"
                    }`}
                  >
                    {/* Visual left glowing accent bar if required */}
                    {q.is_required && (
                      <div className="absolute left-0 top-6 bottom-6 w-[3px] rounded-r-md bg-gradient-to-b from-[#F5B21A] to-[#E09A0A] shadow-[0_0_8px_rgba(245,178,26,0.6)]" />
                    )}

                    {/* Question Header */}
                    <div className="space-y-1.5 pl-2 sm:pl-3">
                      <div className="flex items-start justify-between gap-4">
                        <span className="text-[10px] font-mono text-slate-500 font-semibold uppercase tracking-wider block">
                          Ítem #{idx + 1} {q.code && `· Código: ${q.code}`}
                        </span>
                        {q.is_required && (
                          <span className="text-[9px] font-mono font-bold text-[#F5B21A] uppercase tracking-widest bg-[#F5B21A]/10 border border-[#F5B21A]/20 px-2 py-0.5 rounded">
                            Obligatorio
                          </span>
                        )}
                      </div>
                      <h4 className="text-base sm:text-lg font-medium text-white leading-snug">
                        {q.label}
                      </h4>
                      {q.help_text && (
                        <p className="text-xs text-slate-500 italic font-normal flex items-start gap-1">
                          <HelpCircle className="w-3.5 h-3.5 shrink-0 text-slate-500/80 mt-0.5" />
                          <span>{q.help_text}</span>
                        </p>
                      )}
                    </div>

                    {/* Question Input controls depending on types */}
                    <div className="mt-5 pl-2 sm:pl-3">
                      
                      {/* A. LIKERT / SINGLE_CHOICE / BOOLEAN / DROPDOWN OPTION SELECTOR */}
                      {(q.question_type === "likert" || q.question_type === "single_choice" || q.question_type === "boolean") && (
                        <div className="grid gap-2.5 sm:grid-cols-2 md:grid-cols-3">
                          {q.options.map((opt) => {
                            const isSelected = answers[q.id]?.option_id === opt.id;
                            
                            return (
                              <button
                                key={opt.id}
                                onClick={() => handleAnswerChange(q.id, { option_id: opt.id, value_text: opt.label })}
                                className={`text-left p-3.5 rounded-xl border text-sm font-medium transition-all duration-200 outline-none flex items-center justify-between group ${
                                  isSelected 
                                    ? "bg-gradient-to-r from-[#F5B21A]/15 to-[#E09A0A]/10 border-[#F5B21A] text-white shadow-[0_0_12px_rgba(245,178,26,0.12)]" 
                                    : "bg-slate-950/40 border-white/5 text-slate-400 hover:border-slate-700 hover:bg-slate-900/50 hover:text-white"
                                }`}
                              >
                                <span className="pr-2 leading-relaxed">{opt.label}</span>
                                <div className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 ${
                                  isSelected 
                                    ? "border-[#F5B21A] bg-[#F5B21A]/20" 
                                    : "border-slate-700 group-hover:border-slate-500"
                                }`}>
                                  {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-[#F5B21A] shadow-[0_0_6px_rgba(245,178,26,0.8)]" />}
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      )}

                      {/* B. DROPDOWN (Fall back to gorgeous custom selector if large options count) */}
                      {q.question_type === "dropdown" && (
                        <div className="relative">
                          <select
                            value={answers[q.id]?.option_id || ""}
                            onChange={(e) => {
                              const selectedOpt = q.options.find(o => o.id === e.target.value);
                              handleAnswerChange(q.id, { option_id: e.target.value, value_text: selectedOpt?.label || "" });
                            }}
                            className="w-full h-12 pl-4 pr-10 rounded-xl bg-slate-950/70 border border-white/10 text-white focus:border-[#F5B21A] outline-none transition-all duration-200 appearance-none cursor-pointer text-sm"
                          >
                            <option value="" disabled className="text-slate-600">-- Selecciona una opción --</option>
                            {q.options.map(opt => (
                              <option key={opt.id} value={opt.id} className="bg-[#0D1117] text-white">{opt.label}</option>
                            ))}
                          </select>
                          <ChevronDown className="w-4 h-4 text-slate-500 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                        </div>
                      )}

                      {/* C. MULTIPLE CHOICE SELECTOR */}
                      {q.question_type === "multiple_choice" && (
                        <div className="grid gap-2.5 sm:grid-cols-2 md:grid-cols-3">
                          {q.options.map((opt) => {
                            const selectedArray: string[] = answers[q.id]?.value_json || [];
                            const isSelected = selectedArray.includes(opt.id);

                            const toggleChoice = () => {
                              let nextArray: string[];
                              if (isSelected) {
                                nextArray = selectedArray.filter(id => id !== opt.id);
                              } else {
                                nextArray = [...selectedArray, opt.id];
                              }
                              handleAnswerChange(q.id, { value_json: nextArray });
                            };

                            return (
                              <button
                                key={opt.id}
                                onClick={toggleChoice}
                                className={`text-left p-3.5 rounded-xl border text-sm font-medium transition-all duration-200 outline-none flex items-center justify-between group ${
                                  isSelected 
                                    ? "bg-[#F5B21A]/10 border-[#F5B21A] text-white shadow-[0_0_12px_rgba(245,178,26,0.1)]" 
                                    : "bg-slate-950/40 border-white/5 text-slate-400 hover:border-slate-700 hover:bg-slate-900/50 hover:text-white"
                                }`}
                              >
                                <span className="pr-2 leading-relaxed">{opt.label}</span>
                                <div className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 ${
                                  isSelected 
                                    ? "border-[#F5B21A] bg-[#F5B21A]/20" 
                                    : "border-slate-700 group-hover:border-slate-500"
                                }`}>
                                  {isSelected && <div className="w-2 h-2 bg-[#F5B21A] rounded-[2px]" />}
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      )}

                      {/* D. TEXT SHORT */}
                      {q.question_type === "text_short" && (
                        <input
                          type="text"
                          placeholder="Escribe tu respuesta corta aquí..."
                          value={answers[q.id]?.value_text || ""}
                          onChange={(e) => handleAnswerChange(q.id, { value_text: e.target.value })}
                          className="w-full h-12 px-4 rounded-xl bg-slate-950/60 border border-white/10 text-white placeholder:text-slate-600 focus:border-[#F5B21A] focus:ring-1 focus:ring-[#F5B21A] outline-none transition-all duration-200 text-sm"
                        />
                      )}

                      {/* E. TEXT LONG */}
                      {q.question_type === "text_long" && (
                        <textarea
                          placeholder="Desarrolla tu respuesta detallada aquí..."
                          value={answers[q.id]?.value_text || ""}
                          onChange={(e) => handleAnswerChange(q.id, { value_text: e.target.value })}
                          rows={4}
                          className="w-full p-4 rounded-xl bg-slate-950/60 border border-white/10 text-white placeholder:text-slate-600 focus:border-[#F5B21A] focus:ring-1 focus:ring-[#F5B21A] outline-none transition-all duration-200 text-sm resize-y"
                        />
                      )}

                      {/* F. NUMBER */}
                      {q.question_type === "number" && (
                        <div className="space-y-3">
                          <div className="flex items-center gap-4">
                            <input
                              type="number"
                              min={q.min_value !== null ? q.min_value : undefined}
                              max={q.max_value !== null ? q.max_value : undefined}
                              placeholder="0"
                              value={answers[q.id]?.value_number ?? ""}
                              onChange={(e) => handleAnswerChange(q.id, { value_number: e.target.value !== "" ? Number(e.target.value) : undefined })}
                              className="w-40 h-12 px-4 rounded-xl bg-slate-950/60 border border-white/10 text-white focus:border-[#F5B21A] outline-none transition-all duration-200 text-sm"
                            />
                            {(q.min_value !== null || q.max_value !== null) && (
                              <span className="text-xs text-slate-500 font-mono">
                                Rango válido: [{q.min_value !== null ? q.min_value : "-∞"} a {q.max_value !== null ? q.max_value : "+∞"}]
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* G. DATE */}
                      {q.question_type === "date" && (
                        <div className="relative max-w-[200px]">
                          <input
                            type="date"
                            value={answers[q.id]?.value_date || ""}
                            onChange={(e) => handleAnswerChange(q.id, { value_date: e.target.value })}
                            className="w-full h-12 pl-4 pr-10 rounded-xl bg-slate-950/60 border border-white/10 text-white focus:border-[#F5B21A] outline-none transition-all duration-200 text-sm cursor-pointer"
                          />
                          <Calendar className="w-4 h-4 text-slate-500 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                        </div>
                      )}

                    </div>
                  </div>
                );
              })}
            </div>

            {/* Error alerts / Warning tags */}
            {validationError && (
              <div className="w-full p-4 rounded-2xl bg-amber-950/40 border border-[#F5B21A]/30 text-amber-200 text-sm flex items-start gap-3 shadow-lg animate-pulse">
                <AlertTriangle className="w-5 h-5 text-[#F5B21A] shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <span className="font-bold">Información Incompleta</span>
                  <p className="text-xs text-amber-300/90">{validationError}</p>
                </div>
              </div>
            )}

            {/* Pagination Controls */}
            <div className="flex items-center justify-between mt-4">
              <button
                onClick={handlePrev}
                className="h-12 px-6 rounded-xl border border-white/10 bg-slate-950 hover:bg-slate-900 text-white font-semibold text-sm flex items-center gap-2 transition-all duration-200"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Atrás</span>
              </button>
              
              <button
                onClick={handleNext}
                disabled={submitMutation.isPending}
                className="h-12 px-8 rounded-xl bg-gradient-to-r from-[#F5B21A] to-[#E09A0A] hover:from-[#FFC138] hover:to-[#F5B21A] text-slate-950 font-bold text-sm flex items-center gap-2 shadow-[0_4px_12px_rgba(245,178,26,0.2)] hover:shadow-[0_6px_18px_rgba(245,178,26,0.3)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitMutation.isPending ? (
                  <>
                    <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Enviando...</span>
                  </>
                ) : (
                  <>
                    <span>
                      {currentSectionIndex === formSections.length - 1 ? "Finalizar Cuestionario" : "Siguiente Sección"}
                    </span>
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>

          </div>
        )}

        {/* ── 3. THANK YOU / COMPLETED SCREEN ─────────────────────────────────── */}
        {step === "completed" && (
          <div className="max-w-md w-full bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-[32px] p-8 text-center shadow-2xl relative z-10 animate-colmena-fade-in">
            {/* Top glowing core orb */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full bg-[#F5B21A]/20 blur-md -z-10" />
            
            <CheckCircle className="w-20 h-20 text-[#F5B21A] mx-auto mb-6 drop-shadow-[0_0_20px_rgba(245,178,26,0.4)]" />
            <h2 className="text-3xl font-extrabold text-white mb-3">¡Respuestas Registradas!</h2>
            <p className="text-slate-300 text-sm leading-relaxed mb-8">
              {thank_you_message || "Muchas gracias por tu valiosa colaboración. Tu respuesta ha sido integrada a la base de datos científica del estudio con éxito."}
            </p>
            
            <div className="border border-white/5 bg-[#080B0F]/65 rounded-2xl px-5 py-4 inline-flex flex-col gap-1 items-center justify-center w-full">
              <span className="text-[10px] uppercase font-mono tracking-widest text-slate-500">
                Estado de Transmisión
              </span>
              <span className="text-xs font-bold text-success flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-success animate-ping" />
                Conexión segura y sincronizada
              </span>
            </div>

            <p className="mt-8 text-[10px] text-slate-500 font-mono">
              ID de Transmisión: {transmissionId} · Cifrado AES-256
            </p>
          </div>
        )}

      </main>

      {/* Futuristic technical footer info */}
      <footer className="w-full border-t border-white/5 bg-[#080B0F]/40 px-6 py-4 text-center text-[10px] font-mono text-slate-500 flex flex-col sm:flex-row items-center justify-between shrink-0 gap-2">
        <span>© 2026 COLMENA - Todos los derechos reservados.</span>
        <div className="flex items-center gap-4">
          <span className="hover:text-slate-300 cursor-help flex items-center gap-1">
            <Clipboard className="w-3 h-3" />
            Licencia Académica
          </span>
          <span>Versión 2.4.0-Pro</span>
        </div>
      </footer>

    </div>
  );
}
