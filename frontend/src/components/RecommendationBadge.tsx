import type { RecommendationLabel } from "@/types";
import "./RecommendationBadge.css";

const VARIANT: Record<RecommendationLabel, string> = {
  "Recomendado": "rec--recommended",
  "Avaliar": "rec--review",
  "Baixa compatibilidade": "rec--low",
  "Requisito obrigatório ausente": "rec--missing",
};

export function RecommendationBadge({ label }: { label: RecommendationLabel | null }) {
  if (!label) {
    return <span className="rec rec--empty">Por analisar</span>;
  }
  return (
    <span className={`rec ${VARIANT[label]}`}>
      {label === "Requisito obrigatório ausente"
        ? "Requisitos obrigatórios por comprovar"
        : label}
    </span>
  );
}