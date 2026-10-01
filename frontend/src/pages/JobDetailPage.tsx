import { useRef, useState, type FormEvent } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiErrorMessage } from "@/lib/api";
import { AnalysisStatusBadge } from "@/components/AnalysisStatusBadge";
import { analysisPresentation } from "@/lib/analysisPresentation";
import { JobCreatePage } from "./JobCreatePage";
import { QuestionnaireEditor } from "@/components/QuestionnaireEditor";
import type {
  ApplicationDetail,
  JobDetail,
  JobRequirement,
  RankingItem,
  RequirementCategory,
} from "@/types";
import "./JobDetail.css";

type Tab = "overview" | "requirements" | "candidates" | "ranking" | "questionnaire";

const CATEGORY_LABELS: Record<RequirementCategory, string> = {
  education: "Formação",
  experience: "Experiência",
  technical_skill: "Competência técnica",
  technology: "Tecnologia",
  tool: "Ferramenta",
  language: "Idioma",
  certification: "Certificação",
  soft_skill: "Competência comportamental",
  other: "Outro",
};

export function JobDetailPage() {
  const { jobId } = useParams();
  const [tab, setTab] = useState<Tab>("overview");
  const [questionnaireDirty, setQuestionnaireDirty] = useState(false);
  const queryClient = useQueryClient();

  const { data: job, isLoading, isError, refetch } = useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => (await api.get<JobDetail>(`/jobs/${jobId}`)).data,
  });

  const publishMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${jobId}/publish`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });
  const closeMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${jobId}/close`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });

  if (isLoading) {
    return (
      <div className="jd-loading" role="status" aria-label="A carregar vaga">
        <span className="jd-loading__bar jd-loading__bar--title" />
        <span className="jd-loading__bar jd-loading__bar--meta" />
        <span className="jd-loading__panel" />
      </div>
    );
  }

  if (isError || !job) {
    return (
      <div className="jd-load-error" role="alert">
        <span className="material-symbols-outlined" aria-hidden="true">cloud_off</span>
        <p>Não foi possível carregar esta vaga.</p>
        <button type="button" onClick={() => void refetch()}>Tentar novamente</button>
      </div>
    );
  }

  return (
    <div className="job-detail">
      <div className="job-detail__header">
        <div>
          <h1 className="job-detail__title">{job.title}</h1>
          <p className="job-detail__subtitle">
            {job.code} · {job.department ?? "Sem departamento"} ·{" "}
            {job.location ?? "Sem localização"}
          </p>
        </div>
        <div className="job-detail__actions">
          {job.status === "draft" && (
            <button
              onClick={() => publishMutation.mutate()}
              disabled={publishMutation.isPending}
              className="jd-btn jd-btn--primary"
            >
              {publishMutation.isPending ? "A publicar..." : "Publicar vaga"}
            </button>
          )}
          {job.status === "published" && (
            <button
              onClick={() => closeMutation.mutate()}
              disabled={closeMutation.isPending}
              className="jd-btn jd-btn--secondary"
            >
              {closeMutation.isPending ? "A encerrar..." : "Encerrar vaga"}
            </button>
          )}
        </div>
      </div>

      {publishMutation.isError && (
        <p className="job-detail__error" role="alert">
          {apiErrorMessage(publishMutation.error, "Não foi possível publicar a vaga.")}
        </p>
      )}
      {closeMutation.isError && (
        <p className="job-detail__error" role="alert">
          {apiErrorMessage(closeMutation.error, "Não foi possível encerrar a vaga.")}
        </p>
      )}

      <div className="job-detail__tabs">
        {([
          ["overview", "Visão geral"],
          ["requirements", "Requisitos"],
          ["candidates", "Candidatos"],
          ["ranking", "Ranking"],
          ["questionnaire", "Questionário"],
        ] as [Tab, string][]).map(([value, label]) => (
          <button
            key={value}
            onClick={() => {
              if (
                !questionnaireDirty ||
                value === tab ||
                window.confirm("Descartar alterações não guardadas do questionário?")
              )
                setTab(value);
            }}
            className={`job-detail__tab ${tab === value ? "is-active" : ""}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewTab job={job} />}
      {tab === "requirements" && <RequirementsTab job={job} jobId={jobId!} />}
      {tab === "candidates" && <CandidatesTab jobId={jobId!} />}
      {tab === "ranking" && <RankingTab jobId={jobId!} />}
      {tab === "questionnaire" && (
        <QuestionnaireEditor key={job.id} job={job} onDirty={setQuestionnaireDirty} />
      )}
    </div>
  );
}

/* ===================== Overview ===================== */

function OverviewTab({ job }: { job: JobDetail }) {
  const [editing, setEditing] = useState(false);
  const queryClient = useQueryClient();

  if (editing)
    return (
      <>
        <button className="jd-btn jd-btn--secondary" onClick={() => setEditing(false)}>
          Cancelar edição
        </button>
        <JobCreatePage
          job={job}
          onSaved={() => {
            queryClient.invalidateQueries();
            setEditing(false);
          }}
        />
      </>
    );

  return (
    <div className="jd-card">
      <button className="jd-btn jd-btn--ghost" onClick={() => setEditing(true)}>
        Editar vaga
      </button>

      <p className="jd-overview__label" style={{ marginTop: "0.5rem" }}>
        Versão dos critérios: <span className="jd-overview__value">{job.criteria_version}</span>
      </p>

      <div style={{ marginTop: "1rem" }}>
        <h3 className="jd-overview__section-title">Descrição</h3>
        <p className="jd-overview__description">{job.description}</p>
      </div>

      <div className="jd-overview__metric">
        <div>
          <span className="jd-overview__label">Experiência mínima: </span>
          <span className="jd-overview__value">{job.min_experience_years} ano(s)</span>
        </div>
        <div>
          <span className="jd-overview__label">Formação: </span>
          <span className="jd-overview__value">{job.education_level ?? "Não especificada"}</span>
        </div>
      </div>
    </div>
  );
}

/* ===================== Requirements ===================== */

function RequirementsTab({ job, jobId }: { job: JobDetail; jobId: string }) {
  const queryClient = useQueryClient();
  const [requirementsFile, setRequirementsFile] = useState<File | null>(null);
  const importMutation = useMutation({
    mutationFn: async () => {
      if (!requirementsFile) throw new Error("Seleccione um TXT.");
      const data = new FormData();
      data.append("file", requirementsFile);
      return (await api.post<{ imported: number; skipped: number }>(`/jobs/${jobId}/requirements/import`, data)).data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    expected_level: "intermediate",
    category: "technical_skill" as RequirementCategory,
    weight: 0.1,
    is_mandatory: false,
  });

  const addMutation = useMutation({
    mutationFn: () =>
      editingId
        ? api.put(`/requirements/${editingId}`, form)
        : api.post(`/jobs/${jobId}/requirements`, form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      setForm({
        name: "",
        description: "",
        expected_level: "intermediate",
        category: "technical_skill",
        weight: 0.1,
        is_mandatory: false,
      });
      setEditingId(null);
      setShowForm(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (requirementId: number) => api.delete(`/requirements/${requirementId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });

  const totalWeight = job.requirements.reduce((sum, r) => sum + r.weight, 0);

  return (
    <div>
      <form className="jd-form" onSubmit={(event) => { event.preventDefault(); importMutation.mutate(); }}>
        <label className="jd-field">
          <span>Importar requisitos de TXT</span>
          <input type="file" accept=".txt,text/plain" disabled={importMutation.isPending}
            onChange={(event) => { setRequirementsFile(event.target.files?.[0] ?? null); importMutation.reset(); }} />
        </label>
        <p style={{ gridColumn: "1 / -1" }}>Um requisito por linha, até 100 KB. Os requisitos existentes são mantidos e os repetidos são ignorados. Após importar, reveja as categorias, pesos e requisitos obrigatórios.</p>
        <div style={{ gridColumn: "1 / -1" }}>
          <a className="jd-btn jd-btn--ghost" href={`${import.meta.env.BASE_URL}modelo-requisitos.txt`} download="modelo-requisitos.txt">Descarregar modelo TXT</a>
          <p>Abra o modelo, substitua os exemplos pelos requisitos da sua vaga e guarde o ficheiro. Depois seleccione-o acima e clique em Importar TXT.</p>
        </div>
        <details style={{ gridColumn: "1 / -1" }}><summary>Exemplo de conteúdo do TXT</summary>
          <pre>{"Licenciatura em Informática\nExperiência de 2 anos com Python\nConhecimentos de PostgreSQL\nInglês avançado"}</pre>
          <p>Categoria inicial: Outros; nível: Intermédio; obrigatoriedade: Não. Numa vaga sem requisitos, os pesos são iguais e somam 100%. Ao acrescentar requisitos, cada novo item recebe peso 10%.</p>
        </details>
        <button className="jd-btn jd-btn--primary" type="submit" disabled={!requirementsFile || importMutation.isPending}>
          {importMutation.isPending ? "A importar..." : "Importar TXT"}
        </button>
        {importMutation.error && <p className="jd-alert" role="alert">{apiErrorMessage(importMutation.error, "Não foi possível importar o TXT.")}</p>}
        {importMutation.isSuccess && <p role="status">{importMutation.data.imported} requisito(s) importado(s); {importMutation.data.skipped} já existente(s). Pode editá-los abaixo.</p>}
      </form>
      <div className="jd-card__toolbar">
        <p className="jd-overview__label">
          Soma dos pesos:{" "}
          <span className={Math.abs(totalWeight - 1) > 0.01 ? "jd-warning" : "jd-overview__value"}>
            {(totalWeight * 100).toFixed(0)}%
          </span>
          {Math.abs(totalWeight - 1) > 0.01 && " — o ideal é somar 100%"}
        </p>
        <button
          className="jd-btn jd-btn--ghost"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? "Cancelar" : "+ Adicionar requisito"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            addMutation.mutate();
          }}
          className="jd-form"
        >
          <label className="jd-field jd-field--span-2">
            <span>Nome</span>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="jd-input"
            />
          </label>

          <label className="jd-field">
            <span>Categoria</span>
            <select
              value={form.category}
              onChange={(e) =>
                setForm({ ...form, category: e.target.value as RequirementCategory })
              }
              className="jd-select"
            >
              {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label className="jd-field">
            <span>Peso (%)</span>
            <input
              type="number"
              min={0}
              max={100}
              value={Math.round(form.weight * 100)}
              onChange={(e) => setForm({ ...form, weight: Number(e.target.value) / 100 })}
              className="jd-input"
            />
          </label>

          <label className="jd-field jd-field--check jd-field--span-3">
            <input
              type="checkbox"
              checked={form.is_mandatory}
              onChange={(e) => setForm({ ...form, is_mandatory: e.target.checked })}
            />
            <span>Obrigatório</span>
          </label>

          <label className="jd-field jd-field--span-3">
            <span>Descrição</span>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="jd-textarea"
            />
          </label>

          <label className="jd-field">
            <span>Nível esperado</span>
            <select
              value={form.expected_level}
              onChange={(e) => setForm({ ...form, expected_level: e.target.value })}
              className="jd-select"
            >
              <option value="basic">Básico</option>
              <option value="intermediate">Intermédio</option>
              <option value="advanced">Avançado</option>
              <option value="expert">Especialista</option>
            </select>
          </label>

          <button type="submit" className="jd-btn jd-btn--primary">
            Guardar requisito
          </button>
        </form>
      )}

      <div className="jd-card jd-card--list">
        {totalWeight <= 0 && (
          <p role="alert" className="jd-alert">
            Defina pelo menos um peso superior a zero para analisar CVs.
          </p>
        )}
        {addMutation.isError && (
          <p role="alert" className="jd-alert">
            {apiErrorMessage(addMutation.error)}
          </p>
        )}
        {deleteMutation.isError && (
          <p role="alert" className="jd-alert">
            {apiErrorMessage(deleteMutation.error)}
          </p>
        )}
        {job.requirements.length === 0 && (
          <p className="jd-card__state">
            Ainda não há requisitos. Adicione pelo menos um antes de publicar a vaga.
          </p>
        )}
        {job.requirements.map((req: JobRequirement) => (
          <div key={req.id} className="jd-card__row">
            <div>
              <span className="jd-name">{req.name}</span>
              <span className="jd-category">{CATEGORY_LABELS[req.category]}</span>
              {req.is_mandatory && <span className="jd-badge-mandatory">Obrigatório</span>}
            </div>
            <div className="jd-list-item__right">
              <button
                className="jd-btn jd-btn--ghost"
                onClick={() => {
                  setEditingId(req.id);
                  setShowForm(true);
                  setForm({
                    name: req.name,
                    description: req.description ?? "",
                    expected_level: req.expected_level,
                    category: req.category,
                    weight: req.weight,
                    is_mandatory: req.is_mandatory,
                  });
                }}
              >
                Editar
              </button>
              <span className="jd-weight">{(req.weight * 100).toFixed(0)}%</span>
              <button
                onClick={() => deleteMutation.mutate(req.id)}
                className="jd-btn jd-btn--ghost jd-link--danger"
              >
                Remover
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ===================== Candidates ===================== */

function CandidatesTab({ jobId }: { jobId: string }) {
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const uploadInFlight = useRef(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [pendingAnalysisIds, setPendingAnalysisIds] = useState<number[]>([]);

  const { data: applications, error: candidatesError } = useQuery({
    queryKey: ["job-candidates", jobId],
    queryFn: async () =>
      (await api.get<ApplicationDetail[]>(`/jobs/${jobId}/candidates`)).data,
    refetchInterval: (query) =>
      query.state.data?.some((app) => ["queued", "running"].includes(app.analysis_status))
        ? 1500
        : false,
  });

  const analyzeMutation = useMutation({
    mutationFn: async (resumeId: number) =>
      api.post(`/cvs/${resumeId}/analysis-executions`, null, {
        headers: { "Idempotency-Key": crypto.randomUUID() },
      }),
    onMutate: async (resumeId: number) => {
      setPendingAnalysisIds((prev) => [...new Set([...prev, resumeId])]);
    },
    onSuccess: async (_, resumeId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["job-candidates", jobId] }),
        queryClient.invalidateQueries({ queryKey: ["job-ranking", jobId] }),
      ]);
      setPendingAnalysisIds((prev) => prev.filter((id) => id !== resumeId));
    },
    onError: (_, resumeId) =>
      setPendingAnalysisIds((prev) => prev.filter((id) => id !== resumeId)),
  });

  function selectCV(selected: File | null) {
    setUploadSuccess(null);
    setUploadError(null);
    if (selected && !/\.(pdf|docx)$/i.test(selected.name)) {
      setFile(null);
      setUploadError("Formato não suportado. Seleccione um PDF ou DOCX.");
      return;
    }
    if (selected && selected.size === 0) {
      setFile(null);
      setUploadError("O ficheiro está vazio. Seleccione outro CV.");
      return;
    }
    setFile(selected);
  }

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    if (uploadInFlight.current) return;
    if (!file) {
      setUploadError("Seleccione ou arraste um CV antes de clicar em Carregar.");
      return;
    }
    uploadInFlight.current = true;
    setUploadError(null);
    setUploadSuccess(null);
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post<ApplicationDetail>(`/jobs/${jobId}/cvs`, formData);
      const key = ["job-candidates", jobId];
      await queryClient.cancelQueries({ queryKey: key });
      queryClient.setQueryData<ApplicationDetail[]>(key, (previous = []) =>
        [data, ...previous.filter((application) => application.id !== data.id)]);
      void queryClient.invalidateQueries({ queryKey: key });
      void queryClient.invalidateQueries({ queryKey: ["job-ranking", jobId] });
      setUploadSuccess(`CV guardado na candidatura de ${data.candidate.name} (${data.candidate.email}). ${data.analysis_status === "queued" ? "Análise em fila." : "Consulte o estado da análise na lista abaixo."}`);
      setFile(null);
      setUploadOpen(false);
    } catch (err) {
      setUploadError(apiErrorMessage(err, "Não foi possível carregar o CV."));
    } finally {
      uploadInFlight.current = false;
      setIsUploading(false);
    }
  }

  return (
    <div>
      <div className="jd-card__toolbar" style={{ justifyContent: "flex-end" }}>
        <button className="jd-btn jd-btn--ghost" disabled={isUploading} onClick={() => { setFile(null); setUploadOpen((v) => !v); }}>
          {uploadOpen ? "Cancelar" : "+ Carregar CV"}
        </button>
      </div>

      {uploadError && <p role="alert" className="jd-alert">{uploadError}</p>}
      {uploadSuccess && <p role="status" className="jd-upload-status">{uploadSuccess}</p>}

      {uploadOpen && (
        <form noValidate onSubmit={handleUpload} className="jd-form jd-form--3col"
          aria-busy={isUploading}
          onDragOver={(event) => { event.preventDefault(); }}
          onDrop={(event) => {
            event.preventDefault();
            if (isUploading) return;
            if (event.dataTransfer.files.length !== 1) {
              setUploadError("Arraste apenas um CV de cada vez.");
              return;
            }
            selectCV(event.dataTransfer.files[0]);
          }}>
          <p style={{ gridColumn: "1 / -1" }}>O nome e o e-mail serão lidos automaticamente do CV. Inclua um único e-mail de contacto do candidato em texto legível. Se o nome não for identificado, aparecerá como “Nome não identificado”.</p>
          <label className="jd-field">
            <span>Seleccione ou arraste aqui o CV (PDF ou DOCX)</span>
            <input
              disabled={isUploading}
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => selectCV(e.target.files?.[0] ?? null)}
              className="jd-input"
            />
          </label>
          <p role="status" style={{ gridColumn: "1 / -1" }}>{isUploading ? "A enviar e validar o CV. Aguarde a confirmação." : file ? `Seleccionado: ${file.name}. Clique em Carregar para enviar.` : "Nenhum ficheiro seleccionado."}</p>
          <button type="submit" disabled={isUploading} className="jd-btn jd-btn--primary">
            {isUploading ? "A carregar..." : "Carregar"}
          </button>
        </form>
      )}

      <div className="jd-card jd-card--list">
        {applications?.length === 0 && (
          <p className="jd-card__state">Ainda não há candidaturas para esta vaga.</p>
        )}
        {(candidatesError || analyzeMutation.isError) && (
          <p role="alert" className="jd-alert">
            {apiErrorMessage(candidatesError || analyzeMutation.error)}
          </p>
        )}
        {applications?.map((app) => (
          <div key={app.id} className="jd-card__row">
            <div>
              <Link
                to={`/jobs/${jobId}/applications/${app.id}`}
                className="jd-name jd-link"
              >
                {app.candidate.name}
              </Link>
              <p className="jd-email">{app.candidate.email}</p>
            </div>
            <div className="jd-list-item__right">
              <AnalysisStatusBadge
                value={
                  pendingAnalysisIds.includes(app.latest_resume_id ?? -1)
                    ? { ...app, analysis_status: "queued" }
                    : app
                }
              />
              {app.score !== null && (
                <span className="jd-score">{app.score.toFixed(0)}%</span>
              )}
              {analysisPresentation(app).action === "view" ? (
                <Link to={`/jobs/${jobId}/applications/${app.id}`} className="jd-link">
                  Ver análise
                </Link>
              ) : (
                analysisPresentation(app).action !== "busy" && (
                  <button
                    onClick={() =>
                      app.latest_resume_id && analyzeMutation.mutate(app.latest_resume_id)
                    }
                    disabled={
                      analyzeMutation.isPending ||
                      !app.latest_resume_id ||
                      pendingAnalysisIds.includes(app.latest_resume_id)
                    }
                    className="jd-btn jd-btn--ghost"
                  >
                    {pendingAnalysisIds.includes(app.latest_resume_id ?? -1)
                      ? "Em fila..."
                      : analysisPresentation(app).actionLabel}
                  </button>
                )
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ===================== Ranking ===================== */

const FILTERS: [string, string][] = [
  ["", "Todos"],
  ["recomendado", "Recomendado"],
  ["compatibilidade_parcial", "Compatibilidade parcial"],
  ["baixa_compatibilidade", "Baixa compatibilidade"],
  ["requisito_obrigatorio_ausente", "Obrigatório ausente"],
];

function RankingTab({ jobId }: { jobId: string }) {
  const [filter, setFilter] = useState("");

  const { data: ranking, error: rankingError } = useQuery({
    queryKey: ["job-ranking", jobId, filter],
    queryFn: async () =>
      (
        await api.get<RankingItem[]>(`/jobs/${jobId}/ranking`, {
          params: filter ? { filter } : {},
        })
      ).data,
    refetchInterval: 2000,
  });

  return (
    <div>
      <div className="jd-filters">
        {FILTERS.map(([value, label]) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`jd-filter ${filter === value ? "is-active" : ""}`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="jd-card jd-card--list">
        {rankingError && (
          <p role="alert" className="jd-alert">
            {apiErrorMessage(rankingError)}
          </p>
        )}
        {ranking?.length === 0 && (
          <p className="jd-card__state">Nenhum candidato nesta categoria.</p>
        )}
        {ranking?.map((item, index) => (
          <Link
            key={item.application_id}
            to={`/jobs/${jobId}/applications/${item.application_id}`}
            className="jd-list-item"
          >
            <div className="jd-list-item__left">
              <span className="jd-rank">{index + 1}.</span>
              <div>
                <p className="jd-name">{item.candidate_name}</p>
                <p className="jd-email">{item.candidate_email}</p>
              </div>
            </div>
            <div className="jd-list-item__right">
              <AnalysisStatusBadge value={item} />
              <span className="jd-score">
                {item.score !== null ? `${item.score.toFixed(0)}%` : "—"}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
