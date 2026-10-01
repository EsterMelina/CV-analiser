export interface AnalysisOverview {
  analysis_status: string;
  analysis_method?: string | null;
  analysis_error?: string | null;
  recommendation_label?: string | null;
  stale?: boolean;
}

export function analysisPresentation(value: AnalysisOverview) {
  const state = value.analysis_status;
  if (state === "queued" || state === "running") return {
    label: state === "queued" ? "Em fila" : "A analisar", action: "busy", actionLabel: "Aguardar análise",
  };
  if (state === "error") return {label: "Falha na análise", action: "retry", actionLabel: "Tentar novamente"};
  if (value.stale || state === "stale") return {label: "Análise desactualizada", action: "refresh", actionLabel: "Actualizar análise"};
  if (state === "pending") return {label: "Por analisar", action: "analyze", actionLabel: "Analisar"};
  const labels: Record<string, string> = {
    review_required: "Aguarda revisão", reviewed: "Revisto", not_evaluable: "Documento não avaliável",
    "legacy-unverified": "Histórico não verificado", completed: value.recommendation_label ?? "Análise concluída",
  };
  return {label: value.analysis_method?.startsWith("mock") ? "Simulação concluída — sem avaliação real" :
    labels[state] ?? "Estado de análise desconhecido", action: "view", actionLabel: "Ver análise"};
}
