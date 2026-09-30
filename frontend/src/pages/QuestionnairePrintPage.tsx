import { useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, apiErrorMessage } from "@/lib/api";
import { QuestionnaireSheet, type SheetData } from "@/components/QuestionnaireSheet";

export function QuestionnairePrintPage() {
  const { versionId } = useParams();
  const [params] = useSearchParams();
  const mode = params.get("mode") === "guide" ? "guide" : "questions";
  const {data, error} = useQuery({queryKey: ["questionnaire-print", versionId, mode],
    queryFn: async () => (await api.get<SheetData>(`/questionnaire-versions/${versionId}/print`, {params: {mode}})).data});
  if (error) return <p role="alert">{apiErrorMessage(error)}</p>;
  if (!data) return <p>A preparar documento...</p>;
  return <main><button className="no-print" onClick={() => window.print()}>Imprimir / Guardar em PDF</button><QuestionnaireSheet data={data} /></main>;
}
