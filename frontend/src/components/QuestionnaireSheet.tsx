import React from "react";

export interface PrintableQuestion { prompt: string; options: string[]; expected_answer?: string; rubric?: string; correct_index?: number | null }
export interface SheetData { job: string; code: string; version: number; status: string; mode: "questions" | "guide"; questions: PrintableQuestion[] }

export function QuestionnaireSheet({ data }: { data: SheetData }) {
  return <article className="questionnaire-sheet">
    <header><h1>{data.job}</h1><p>{data.code} · Versão {data.version} · {data.status === "approved" ? "Aprovada" : "RASCUNHO / NÃO APROVADA"}</p>
      <h2>{data.mode === "guide" ? "Guia do recrutador — uso interno" : "Folha de perguntas"}</h2></header>
    <ol>{data.questions.map((question, index) => <li key={index} className="print-question">
      <h3>{question.prompt}</h3>
      {question.options.length > 0 ? <ol type="A">{question.options.map((option, i) => <li key={i}>{option}</li>)}</ol> : data.mode === "questions" && <div className="answer-space" />}
      {data.mode === "guide" && <div><p><strong>Resposta esperada:</strong> {question.expected_answer}</p>
        {question.correct_index != null && <p>Alternativa correcta: {question.correct_index + 1}</p>}
        <p><strong>Critérios:</strong> {question.rubric}</p></div>}
    </li>)}</ol>
  </article>;
}
