import { analysisPresentation, type AnalysisOverview } from "@/lib/analysisPresentation";
import "./AnalysisStatusBadge.css";

export function AnalysisStatusBadge({ value }: { value: AnalysisOverview }) {
  const presentation = analysisPresentation(value);
  const label = presentation.label.toLowerCase();

  // Mapear label para variante cromática
  let variant = "neutral";
  if (label.includes("recomendado") || label.includes("concluída") || label.includes("sucesso"))
    variant = "success";
  else if (label.includes("parcial") || label.includes("aguarda") || label.includes("avaliação"))
    variant = "warning";
  else if (label.includes("ausente") || label.includes("erro") || label.includes("falhou"))
    variant = "danger";
  else if (
    label.includes("fila") ||
    label.includes("análise") ||
    label.includes("processamento") ||
    label.includes("running")
  )
    variant = "info";

  return (
    <span
      title={value.analysis_error ?? undefined}
      className={`asb asb--${variant}`}
    >
      {presentation.label}
    </span>
  );
}