import type { RecommendationLabel } from "@/types";

const STYLES: Record<RecommendationLabel, string> = {
  "Recomendado": "bg-brand-soft text-brand-dark",
  "Avaliar": "bg-warn-soft text-warn",
  "Baixa compatibilidade": "bg-ink/5 text-ink-soft",
  "Requisito obrigatório ausente": "bg-danger-soft text-danger",
};

export function RecommendationBadge({ label }: { label: RecommendationLabel | null }) {
  if (!label) {
    return (
      <span className="inline-flex items-center rounded-sm px-2 py-0.5 text-sm bg-ink/5 text-ink-faint">
        Por analisar
      </span>
    );
  }
  return (
    <span className={`inline-flex items-center rounded-sm px-2 py-0.5 text-sm font-medium ${STYLES[label]}`}>
      {label === "Requisito obrigatório ausente" ? "Requisitos obrigatórios por comprovar" : label}
    </span>
  );
}
