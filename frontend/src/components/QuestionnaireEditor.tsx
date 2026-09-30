import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiErrorMessage } from "@/lib/api";
import type { JobDetail } from "@/types";

type Question = { key: string; requirement_id: number; category: string; format: "open" | "single_choice";
  prompt: string; options: string[]; correct_index: number | null; expected_answer: string; rubric: string; provenance: string };
type Content = { language: "pt" | "en"; questions: Question[] };
type Version = { id: number; number: number; revision: number; status: string; criteria_version: number;
  stale: boolean; created_by_id: number; approved_by_id: number | null; approved_at: string | null; content: Content };
type Execution = { id: string; status: string; error: string | null; provider: string | null;
  result: {content: Content; version_id?: number; simulated: boolean} | null };

const areas: Record<string, string> = {education: "Formação", experience: "Experiência", technical_skill: "Competências técnicas",
  technology: "Tecnologias", tool: "Ferramentas", language: "Idiomas", certification: "Certificações",
  soft_skill: "Competências comportamentais", other: "Outros requisitos"};
const versionStatuses: Record<string, string> = {draft: "Rascunho", approved: "Aprovado", archived: "Arquivado"};

export function QuestionnaireEditor({ job, onDirty }: { job: JobDetail; onDirty: (value: boolean) => void }) {
  const queryClient = useQueryClient();
  const [active, setActive] = useState<Version | null>(null);
  const [content, setContent] = useState<Content>({ language: "pt", questions: [] });
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [proposal, setProposal] = useState<Execution | null>(null);
  const [count, setCount] = useState(5);
  const [format, setFormat] = useState<"open" | "single_choice">("open");
  const [difficulty, setDifficulty] = useState("intermediate");
  const [category, setCategory] = useState("");
  const [visibleAnswers, setVisibleAnswers] = useState<string[]>([]);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [requirementIds, setRequirementIds] = useState(job.requirements.map(r => r.id));
  const { data: versions, error: loadError } = useQuery({queryKey: ["questionnaires", job.id],
    queryFn: async () => (await api.get<Version[]>(`/jobs/${job.id}/questionnaires`)).data});
  const { data: execution, error: executionError } = useQuery({queryKey: ["execution", executionId], enabled: !!executionId,
    queryFn: async () => (await api.get<Execution>(`/executions/${executionId}`)).data,
    refetchInterval: query => ["queued", "running"].includes(query.state.data?.status ?? "queued") ? 1200 : false});
  const running = !!executionId && !executionError && (!execution || ["queued", "running"].includes(execution.status));
  function open(version: Version) { setActive(version); setContent(structuredClone(version.content)); setDirty(false); setProposal(null); setVisibleAnswers([]); setEditingKey(null); }
  useEffect(() => { if (!active && versions?.length) open(versions[0]); }, [versions]);
  useEffect(() => { onDirty(dirty); return () => onDirty(false); }, [dirty, onDirty]);
  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } };
    const click = (event: MouseEvent) => {
      if (dirty && (event.target as Element).closest("a[href]") && !window.confirm("Existem alterações não guardadas. Sair e descartá-las?")) event.preventDefault();
    };
    window.addEventListener("beforeunload", beforeUnload); document.addEventListener("click", click, true);
    return () => { window.removeEventListener("beforeunload", beforeUnload); document.removeEventListener("click", click, true); };
  }, [dirty]);
  useEffect(() => {
    if (execution?.status === "succeeded" && execution.result) {
      if (execution.result.version_id) {
        void api.get<Version>(`/questionnaire-versions/${execution.result.version_id}`).then(r => open(r.data)).catch(e => setError(apiErrorMessage(e)));
        void queryClient.invalidateQueries({queryKey: ["questionnaires", job.id]});
      } else setProposal(execution);
      setExecutionId(null);
    }
  }, [execution]);
  const editable = active?.status === "draft";
  const update = (next: Content) => { setContent(next); setDirty(true); };
  const changeQuestion = (index: number, patch: Partial<Question>) => update({...content,
    questions: content.questions.map((q, i) => i === index ? {...q, ...patch} : q)});
  async function action(fn: () => Promise<void>) { setBusy(true); setError(""); try { await fn(); } catch(e) { setError(apiErrorMessage(e)); } finally { setBusy(false); } }
  async function save() { if (!active) return; const response = await api.put<Version>(`/questionnaire-versions/${active.id}`,
    {expected_revision: active.revision, content}); open(response.data); await queryClient.invalidateQueries({queryKey: ["questionnaires", job.id]}); }
  async function generate(target?: Question) {
    const response = await api.post<Execution>(`/jobs/${job.id}/questionnaires/generate`, {
      version_id: target || content.questions.length ? active?.id ?? null : null, target_key: target?.key ?? null,
      config: {requirement_ids: target ? [target.requirement_id] : requirementIds, count: target ? 1 : count,
        category: target?.category ?? (category || null), format: target?.format ?? format, difficulty, language: content.language}},
      {headers: {"Idempotency-Key": crypto.randomUUID()}});
    setExecutionId(response.data.id); setProposal(null);
  }
  return <section className="questionnaire-editor space-y-5">
    <p>Gere perguntas para a função de {job.title}, de acordo com a área de avaliação e as competências seleccionadas.</p>
    {(error || loadError || executionError) && <p role="alert">{error || apiErrorMessage(loadError || executionError)}</p>}
    <div className="flex flex-wrap gap-3">
      <label>Versão <select value={active?.id ?? ""} onChange={e => { if (!dirty || window.confirm("Descartar alterações não guardadas?")) { const v = versions?.find(v => v.id === Number(e.target.value)); if(v) open(v); } }}>
        <option value="" disabled>Seleccione</option>{versions?.map(v => <option key={v.id} value={v.id}>v{v.number} — {versionStatuses[v.status] ?? v.status}{v.stale ? " — desactualizada" : ""}</option>)}
      </select></label>
      <button disabled={busy || dirty || running} onClick={() => action(async () => { const r = await api.post<Version>(`/jobs/${job.id}/questionnaires`, {language: content.language, questions: []}); open(r.data); await queryClient.invalidateQueries({queryKey: ["questionnaires", job.id]}); })}>Novo rascunho</button>
      {active && <button disabled={busy || dirty} onClick={() => action(async () => { const r = await api.post<Version>(`/questionnaire-versions/${active.id}/fork`); open(r.data); await queryClient.invalidateQueries({queryKey: ["questionnaires", job.id]}); })}>Copiar para nova versão</button>}
    </div>
    {active?.stale && <p role="status">Critérios alterados. Esta versão conserva os critérios v{active.criteria_version}; crie um novo rascunho para usar os actuais.</p>}
    {active?.approved_at && <p>Aprovada por utilizador {active.approved_by_id} em {new Date(active.approved_at).toLocaleString("pt-PT")}</p>}
    <details className="rounded-lg border border-line bg-canvas p-4" open={!content.questions.length}>
    <summary>Configurar geração de perguntas</summary>
    <fieldset disabled={busy || running || dirty || (!!active && !editable) || !!active?.stale} className="mt-4 border p-4 space-y-3">
      <legend>Proposta de questionário</legend>
      <div className="flex flex-wrap gap-4">
        <label>Área de avaliação <select value={category} onChange={e => {
          const value = e.target.value; setCategory(value);
          setRequirementIds(job.requirements.filter(r => !value || r.category === value).map(r => r.id));
        }}><option value="">Todas as áreas</option>{Array.from(new Set(job.requirements.map(r => r.category))).map(value =>
          <option key={value} value={value}>{areas[value] ?? value}</option>)}</select></label>
        <label>Quantidade <input type="number" min={1} max={30} value={count} onChange={e => setCount(Number(e.target.value))} /></label>
        <label>Formato <select value={format} onChange={e => setFormat(e.target.value as typeof format)}><option value="open">Aberta</option><option value="single_choice">Escolha única</option></select></label>
        <label>Dificuldade <select value={difficulty} onChange={e => setDifficulty(e.target.value)}><option value="basic">Básica</option><option value="intermediate">Intermédia</option><option value="advanced">Avançada</option></select></label>
        <label>Idioma <select value={content.language} onChange={e => setContent({...content, language: e.target.value as "pt" | "en"})}><option value="pt">Português</option><option value="en">English</option></select></label>
      </div>
      <p>Competências e categorias:</p>
      {job.requirements.filter(r => !category || r.category === category).map(r => <label key={r.id} className="inline-block mr-4"><input type="checkbox" checked={requirementIds.includes(r.id)} onChange={e => setRequirementIds(e.target.checked ? [...requirementIds, r.id] : requirementIds.filter(id => id !== r.id))} /> {r.name} ({areas[r.category] ?? r.category})</label>)}
      <button disabled={!requirementIds.length || !Number.isInteger(count) || count < 1 || count > 30} onClick={() => action(() => generate())} className="block text-brand">{content.questions.length ? "Gerar proposta de substituição" : "Gerar perguntas"}</button>
    </fieldset>
    </details>
    {running && <p role="status">{execution?.status === "running" ? "A gerar proposta..." : "Pedido em fila. A aguardar processamento."}</p>}
    {execution?.status === "failed" && <div role="alert">{execution.error}<button onClick={() => action(async () => { await api.post(`/executions/${execution.id}/retry`); await queryClient.invalidateQueries({queryKey: ["execution", execution.id]}); })}>Tentar novamente</button></div>}
    {proposal && <section className="border p-4 space-y-3"><h3>Comparar proposta</h3>
      <div className="grid grid-cols-2 gap-4"><div><h4>Original</h4>{content.questions.map(q => <p key={q.key}>{q.prompt}</p>)}</div>
      <div><h4>Proposta nova</h4>{proposal.result?.content.questions.map(q => <p key={q.key}>{q.prompt}</p>)}</div></div>
      <button disabled={busy || dirty} onClick={() => action(async () => { const r = await api.post<Version>(`/questionnaire-versions/${active!.id}/apply-generation`, {execution_id: proposal.id, expected_revision: active!.revision}); open(r.data); await queryClient.invalidateQueries({queryKey: ["questionnaires", job.id]}); })}>Aplicar proposta</button>
      <button onClick={() => setProposal(null)}>Rejeitar proposta</button></section>}
    {active && <>
      <div className="flex flex-wrap gap-3">{editable && <><button disabled={busy || !dirty} onClick={() => action(save)}>Guardar alterações</button>
        <button disabled={busy || dirty || !content.questions.length} onClick={() => action(async () => { const r = await api.post<Version>(`/questionnaire-versions/${active.id}/approve`, {expected_revision: active.revision}); open(r.data); await queryClient.invalidateQueries({queryKey: ["questionnaires", job.id]}); })}>Aprovar versão revista</button></>}
        <Link target="_blank" to={`/questionnaires/${active.id}/print?mode=questions`}>Folha de perguntas</Link><Link target="_blank" to={`/questionnaires/${active.id}/print?mode=guide`}>Guia do recrutador</Link>
        {active.status !== "archived" && <button disabled={dirty || busy} onClick={() => action(async () => { const r = await api.post<Version>(`/questionnaire-versions/${active.id}/archive`, {expected_revision: active.revision}); open(r.data); await queryClient.invalidateQueries({queryKey: ["questionnaires", job.id]}); })}>Arquivar</button>}
      </div>
      {dirty && <p role="status">Alterações não guardadas.</p>}
      <div className="flex items-center justify-between border-b border-line pb-3"><h3 className="font-semibold">Perguntas do questionário</h3><span className="text-sm text-ink-soft">{content.questions.length} perguntas</span></div>
      {!content.questions.length && <p className="rounded-lg border border-dashed border-line p-8 text-center text-ink-soft">Ainda não existem perguntas. Gere uma proposta ou adicione uma pergunta.</p>}
      {content.questions.map((q, index) => <article key={q.key} className="rounded-lg border border-line bg-surface overflow-hidden">
        <div className="flex flex-wrap items-start gap-4 p-5">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-brand-soft text-sm font-semibold text-brand-dark">{String(index + 1).padStart(2, "0")}</span>
          <div className="min-w-0 flex-1"><p className="text-xs text-ink-soft mb-2">{job.requirements.find(r => r.id === q.requirement_id)?.name} · {q.format === "open" ? "Resposta aberta" : "Escolha única"}</p><h4 className="font-medium whitespace-pre-wrap break-words">{q.prompt}</h4>
            {q.options.length > 0 && <ol className="mt-3 space-y-2 text-sm text-ink-soft">{q.options.map((option, i) => <li key={i}>{String.fromCharCode(65 + i)}. {option}</li>)}</ol>}
          </div>
          <div className="flex gap-2"><button type="button" aria-expanded={visibleAnswers.includes(q.key)} aria-controls={`answer-${q.key}`} onClick={() => setVisibleAnswers(keys => keys.includes(q.key) ? keys.filter(key => key !== q.key) : [...keys, q.key])}>{visibleAnswers.includes(q.key) ? "Ocultar resposta" : "Ver resposta"}</button>
          {editable && <button type="button" disabled={busy} aria-expanded={editingKey === q.key} onClick={() => setEditingKey(editingKey === q.key ? null : q.key)}>{editingKey === q.key ? "Fechar edição" : "Editar"}</button>}</div>
        </div>
        {visibleAnswers.includes(q.key) && <div id={`answer-${q.key}`} className="border-t border-line bg-canvas p-5 space-y-3 text-sm">
          {q.correct_index != null && <p><strong>Alternativa correcta:</strong> {String.fromCharCode(65 + q.correct_index)}. {q.options[q.correct_index]}</p>}
          <div><h5 className="font-semibold mb-1">Resposta esperada</h5><p className="whitespace-pre-wrap">{q.expected_answer || "Resposta de referência ainda não definida."}</p></div>
          <div><h5 className="font-semibold mb-1">Critérios de avaliação</h5><p className="whitespace-pre-wrap text-ink-soft">{q.rubric || "Critérios ainda não definidos."}</p></div>
        </div>}
        {editingKey === q.key && editable && <fieldset disabled={busy} className="border-t border-line p-5 space-y-3">
        <legend>Pergunta {index + 1} · {q.provenance}</legend>
        <label>Competência <select value={q.requirement_id} onChange={e => { const r = job.requirements.find(r => r.id === Number(e.target.value)); if(r) changeQuestion(index, {requirement_id: r.id, category: r.category}); }}>
          {job.requirements.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></label>
        <label className="block">Enunciado<textarea className="w-full border p-2" value={q.prompt} onChange={e => changeQuestion(index, {prompt: e.target.value})} /></label>
        <label>Formato <select value={q.format} onChange={e => changeQuestion(index, e.target.value === "open" ? {format: "open", options: [], correct_index: null} : {format: "single_choice", options: ["Opção A", "Opção B"], correct_index: 0})}><option value="open">Aberta</option><option value="single_choice">Escolha única</option></select></label>
        {q.format === "single_choice" && <><label className="block">Opções (uma por linha)<textarea value={q.options.join("\n")} onChange={e => changeQuestion(index, {options: e.target.value.split("\n")})} /></label>
          <label>Resposta correcta <select value={q.correct_index ?? 0} onChange={e => changeQuestion(index, {correct_index: Number(e.target.value)})}>{q.options.map((o, i) => <option key={i} value={i}>{i + 1}. {o}</option>)}</select></label></>}
        <label className="block">Resposta esperada<textarea className="w-full border p-2" value={q.expected_answer} onChange={e => changeQuestion(index, {expected_answer: e.target.value})} /></label>
        <label className="block">Rubrica / critérios de avaliação<textarea className="w-full border p-2" value={q.rubric} onChange={e => changeQuestion(index, {rubric: e.target.value})} /></label>
        <div className="flex gap-4">{[-1, 1].map(delta => <button key={delta} disabled={index + delta < 0 || index + delta >= content.questions.length} onClick={() => { const questions = [...content.questions]; [questions[index], questions[index + delta]] = [questions[index + delta], questions[index]]; update({...content, questions}); }}>{delta < 0 ? "Subir" : "Descer"}</button>)}
          <button onClick={() => update({...content, questions: content.questions.filter((_, i) => i !== index)})}>Remover</button>
          <button disabled={dirty || running || !!active.stale} onClick={() => action(() => generate(q))}>Propor nova pergunta</button></div>
      </fieldset>}</article>)}
      {editable && <button disabled={!job.requirements.length} onClick={() => { const r = job.requirements[0]; update({...content, questions: [...content.questions,
        {key: crypto.randomUUID(), requirement_id: r.id, category: r.category, format: "open", prompt: "Nova pergunta", options: [], correct_index: null, expected_answer: "", rubric: "", provenance: "manual"}]}); }}>Adicionar pergunta</button>}
    </>}
  </section>;
}
