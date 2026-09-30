import "./QuestionnaireSheet.css";

export interface PrintableQuestion {
  prompt: string;
  options: string[];
  expected_answer?: string;
  rubric?: string;
  correct_index?: number | null;
}

export interface SheetData {
  job: string;
  code: string;
  version: number;
  status: string;
  mode: "questions" | "guide";
  questions: PrintableQuestion[];
}

export function QuestionnaireSheet({ data }: { data: SheetData }) {
  return (
    <article className="qsheet">
      <header className="qsheet__header">
        <h1 className="qsheet__job">{data.job}</h1>
        <p className="qsheet__meta">
          {data.code} · Versão {data.version} ·{" "}
          <strong>{data.status === "approved" ? "Aprovada" : "RASCUNHO / NÃO APROVADA"}</strong>
        </p>
        <h2 className="qsheet__mode">
          {data.mode === "guide"
            ? "Guia do recrutador — uso interno"
            : "Folha de perguntas"}
        </h2>
      </header>

      <ol className="qsheet__questions">
        {data.questions.map((question, index) => (
          <li key={index} className="qsheet__question">
            <h3 className="qsheet__prompt">{question.prompt}</h3>

            {question.options.length > 0 ? (
              <ol type="A" className="qsheet__options">
                {question.options.map((option, i) => (
                  <li key={i}>{option}</li>
                ))}
              </ol>
            ) : (
              data.mode === "questions" && <div className="qsheet__answer-space" />
            )}

            {data.mode === "guide" && (
              <div className="qsheet__guide">
                <p>
                  <strong>Resposta esperada:</strong> {question.expected_answer}
                </p>
                {question.correct_index != null && (
                  <p>Alternativa correcta: {question.correct_index + 1}</p>
                )}
                <p>
                  <strong>Critérios:</strong> {question.rubric}
                </p>
              </div>
            )}
          </li>
        ))}
      </ol>
    </article>
  );
}