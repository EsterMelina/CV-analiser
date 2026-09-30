import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiErrorMessage } from "@/lib/api";
import { InterviewSection } from "@/components/InterviewSection";
import { CompatibilitySummary, type AnalysisRequirement } from "@/components/CompatibilitySummary";
import type { ApplicationDetail } from "@/types";
import { analysisRunning } from "@/lib/analysisRunning";

interface Evidence {requirement_id: number; state: string; explanation: string; citations: {location: string; quote: string}[]}
interface Run {id: number; resume_id: number | null; document_hash: string | null; status: string; score: number | null;
  method: string; policy_version: string; criteria_version: number; stale: boolean; reason: string;
  created_by_id: number; created_at: string; parent_id: number | null;
  sources: {location: string; text: string}[]; evidence: Evidence[];
  requirements: AnalysisRequirement[];
  result: {recommendation?: string | null; summary?: string; profile_scope?: string};
  profile: {skills?: {value: string}[]; education?: {value: string}[]; languages?: {value: string}[];
    experiences?: {employer: string | null; activity: string; start: string | null; end: string | null}[]}}

const states: Record<string, string> = {received: "Recebido", in_evaluation: "Em avaliação", interview_selected: "Seleccionado para entrevista", interviewed: "Entrevistado", hired: "Contratado", rejected: "Rejeitado"};
const evidenceStates: Record<string, string> = {evidenced: "Evidenciado", partial: "Parcial", not_evidenced: "Não evidenciado", contradictory: "Contraditório"};

export function CandidateOverview() {
  const {applicationId, jobId} = useParams();
  const queryClient = useQueryClient();
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [runId, setRunId] = useState<number | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const {data: application, error: appError} = useQuery({queryKey: ["application", applicationId],
    queryFn: async () => (await api.get<ApplicationDetail>(`/applications/${applicationId}`)).data,
    refetchInterval: query => ["queued", "running"].includes(query.state.data?.analysis_status ?? "") ? 1500 : false});
  const {data: configuration, error: configurationError} = useQuery({queryKey: ["analysis-configuration"],
    queryFn: async () => (await api.get<{ready: boolean; message: string | null}>("/analysis-configuration")).data});
  const {data: runs, error: runsError} = useQuery({queryKey: ["analysis-runs", applicationId],
    queryFn: async () => (await api.get<Run[]>(`/applications/${applicationId}/analysis-runs`)).data});
  const {data: execution, error: executionError} = useQuery({queryKey: ["execution", executionId], enabled: !!executionId,
    queryFn: async () => (await api.get(`/executions/${executionId}`)).data,
    refetchInterval: query => ["queued", "running"].includes(query.state.data?.status ?? "queued") ? 1200 : false});
  const selectedResume = resumeId ?? application?.latest_resume_id;
  const run = runs?.find(r => r.id === runId) ?? runs?.find(r => r.resume_id === selectedResume);
  useEffect(() => {
    setResumeId(null); setRunId(null); setExecutionId(null); setError("");
  }, [applicationId]);
  const running = analysisRunning(executionId, execution?.status, application?.analysis_status, !!executionError);
  useEffect(() => {
    if (application?.analysis_execution_id) setExecutionId(application.analysis_execution_id);
  }, [application?.analysis_execution_id]);
  useEffect(() => {
    if (application?.analysis_id) void queryClient.invalidateQueries({queryKey: ["analysis-runs", applicationId]});
  }, [application?.analysis_id, applicationId, queryClient]);

  useEffect(() => { if(execution?.status === "succeeded") { setExecutionId(null); setRunId(execution.result.analysis_id); void queryClient.invalidateQueries(); } }, [execution]);
  useEffect(() => {
    if (execution?.status === "failed") void queryClient.invalidateQueries({queryKey: ["application", applicationId]});
  }, [execution?.status, applicationId, queryClient]);
  async function action(fn: () => Promise<void>) { setError(""); setBusy(true); try { await fn(); } catch(e) { setError(apiErrorMessage(e)); } finally { setBusy(false); } }
  async function analyze() { const response = await api.post(`/cvs/${selectedResume}/analysis-executions`, null,
    {headers: {"Idempotency-Key": crypto.randomUUID()}}); setExecutionId(response.data.id); }
  async function download() {
    const response = await api.get(`/cvs/${selectedResume}/download`, {responseType: "blob"});
    const url = URL.createObjectURL(response.data); const link = document.createElement("a");
    link.href = url; link.download = application?.resumes.find(r => r.id === selectedResume)?.original_filename ?? "cv";
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  if(appError) return <p role="alert">{apiErrorMessage(appError)}</p>;
  if(!application) return <p>A carregar candidatura...</p>;
  return <main className="w-full space-y-5">
    <Link to={`/jobs/${jobId}`}>← Voltar à vaga</Link>
    <h1 className="text-2xl">{application.candidate.name}</h1><p>{application.candidate.email}</p>
    <p>Etapa da candidatura: {states[application.status] ?? application.status}</p>
    {configuration && !configuration.ready && <p role="alert">{configuration.message}</p>}
    {configurationError && <p role="alert">{apiErrorMessage(configurationError)}</p>}
    {executionError && <p role="alert">Não foi possível consultar a análise. {apiErrorMessage(executionError)}</p>}
    {!executionId && application.analysis_error && <p role="alert">{application.analysis_error}</p>}
    {(error || runsError) && <p role="alert">{error || apiErrorMessage(runsError)}</p>}
    <div className="flex flex-wrap items-center gap-3"><label>Documento <select value={selectedResume ?? ""} onChange={e => {setResumeId(Number(e.target.value)); setRunId(null);}}>
      {application.resumes.map((r, i) => <option key={r.id} value={r.id}>v{i + 1} — {r.original_filename}</option>)}</select></label>
      <button disabled={busy} onClick={() => action(download)}>Descarregar CV</button>
      <button disabled={busy || running || !selectedResume || !configuration?.ready} onClick={() => action(analyze)}>
        {running ? "A analisar..." : run && !run.method.startsWith("mock") ? "Reanalisar CV" : "Analisar CV com IA"}</button></div>
    {running && <p role="status">{execution?.status === "running" ?
      execution.result?.progress?.stage === "generating" ?
        `A produzir a avaliação dos requisitos (${Math.floor(execution.result.progress.elapsed_seconds / 60)} min).` :
        "A preparar a comparação do CV. O modelo local pode demorar alguns minutos." : "Análise em fila"}</p>}
    {execution?.status === "failed" && <p role="alert">{execution.error} <button onClick={() => action(async () => { await api.post(`/executions/${execution.id}/retry`); await queryClient.invalidateQueries({queryKey: ["execution", execution.id]}); })}>Tentar novamente</button></p>}
    <label>Histórico <select value={run?.id ?? ""} onChange={e => setRunId(Number(e.target.value))}>
      <option value="" disabled>Seleccione análise</option>{runs?.map(r => <option key={r.id} value={r.id}>#{r.id} · {r.method} · {new Date(r.created_at).toLocaleString("pt-PT")}</option>)}</select></label>
    {!runs?.length && <p>Sem análise. Seleccione um documento e peça nova análise.</p>}
    {run && <section className="space-y-5 rounded-lg border border-line bg-surface p-4 sm:p-6">
      <CompatibilitySummary score={run.score} method={run.method} requirements={run.requirements ?? []} evidence={run.evidence}
        recommendation={run.result?.recommendation} summary={run.result?.summary} />
      <details><summary>Detalhes da análise</summary><p>{run.reason}</p>
      <p>Documento #{run.resume_id ?? "não identificado no histórico"} · Critérios v{run.criteria_version} · Método {run.method} · Política {run.policy_version}</p></details>
      {run.stale && <p role="status">Resultado desactualizado. Existem novos critérios ou uma nova versão do CV.</p>}
      {run.parent_id && <p>Correcção da análise #{run.parent_id}, por utilizador {run.created_by_id}.</p>}
      {!run.method.startsWith("mock") && <>
      <h2 className="text-xl">{run.result?.profile_scope === "supported_requirements" ? "Requisitos comprovados no CV" : "Perfil extraído do CV"}</h2>
      {(["skills", "education", "languages"] as const).map(key => <div key={key}><h3>{{skills: "Competências", education: "Formação", languages: "Idiomas"}[key]}</h3>
        <ul>{run.profile[key]?.map((fact, i) => <li key={i}>{fact.value}</li>)}</ul>{!run.profile[key]?.length && <p>Não determinado</p>}</div>)}
      {!!run.profile.experiences?.length && <h3>Experiência</h3>}{run.profile.experiences?.map((experience, i) => <p key={i}>{experience.employer ?? "Entidade não determinada"}: {experience.activity} ({experience.start ?? "data desconhecida"} — {experience.end ?? "data desconhecida"})</p>)}
      <h2 className="text-xl">Avaliação por requisito</h2><p>A IA comparou os requisitos com o CV. Cada conclusão apresenta a respectiva justificação e os excertos utilizados.</p>
      {run.evidence.map((item) => <div key={item.requirement_id} className="border p-3">
        <h3>{run.requirements?.find(r => r.id === item.requirement_id)?.name ?? `Requisito #${item.requirement_id}`}: {evidenceStates[item.state]}</h3>
        <p>{run.requirements?.find(r => r.id === item.requirement_id)?.description}</p>
        <p>{item.explanation}</p>
        {item.citations.map((citation, i) => <blockquote key={i}><a href={`#source-${run.id}-${citation.location}`}>{citation.location}</a>: <mark>{citation.quote}</mark></blockquote>)}
      </div>)}
      </>}
      <h2>Texto original localizado</h2>{run.sources.map(source => <details key={source.location} id={`source-${run.id}-${source.location}`}><summary>{source.location}</summary><pre className="whitespace-pre-wrap">{source.text}</pre></details>)}
    </section>}
    <InterviewSection key={`interviews-${applicationId}`} applicationId={applicationId!} />
  </main>;
}
