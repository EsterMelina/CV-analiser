import { useState, type FormEvent } from "react";
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

type Tab =
  | "overview"
  | "requirements"
  | "candidates"
  | "ranking"
  | "questionnaire";

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

  const { data: job } = useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => (await api.get<JobDetail>(`/jobs/${jobId}`)).data,
  });

  const publishMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${jobId}/publish`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });
  const closeMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${jobId}/close`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });

  if (!job) return <p className="text-ink-faint text-sm">A carregar...</p>;

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl text-ink mb-1">{job.title}</h1>
          <p className="text-ink-soft text-sm">
            {job.code} · {job.department ?? "Sem departamento"} ·{" "}
            {job.location ?? "Sem localização"}
          </p>
        </div>
        <div className="flex gap-2">
          {job.status === "draft" && (
            <button
              onClick={() => publishMutation.mutate()}
              className="rounded-sm bg-brand text-white px-4 py-2 text-sm font-medium hover:bg-brand-dark transition-colors"
            >
              Publicar vaga
            </button>
          )}
          {job.status === "published" && (
            <button
              onClick={() => closeMutation.mutate()}
              className="rounded-sm border border-line px-4 py-2 text-sm font-medium text-ink-soft hover:bg-canvas transition-colors"
            >
              Encerrar vaga
            </button>
          )}
        </div>
      </div>
      {publishMutation.isError && (
        <p className="text-sm text-danger bg-danger-soft rounded-sm px-3 py-2 mb-4">
          {apiErrorMessage(
            publishMutation.error,
            "Não foi possível publicar a vaga.",
          )}
        </p>
      )}

      <div className="flex gap-1 border-b border-line mb-6">
        {(
          [
            ["overview", "Visão geral"],
            ["requirements", "Requisitos"],
            ["candidates", "Candidatos"],
            ["ranking", "Ranking"],
            ["questionnaire", "Questionário"],
          ] as [Tab, string][]
        ).map(([value, label]) => (
          <button
            key={value}
            onClick={() => {
              if (
                !questionnaireDirty ||
                value === tab ||
                window.confirm(
                  "Descartar alterações não guardadas do questionário?",
                )
              )
                setTab(value);
            }}
            className={`px-4 py-2 text-sm border-b-2 -mb-px transition-colors ${
              tab === value
                ? "border-brand text-ink font-medium"
                : "border-transparent text-ink-soft hover:text-ink"
            }`}
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
        <QuestionnaireEditor
          key={job.id}
          job={job}
          onDirty={setQuestionnaireDirty}
        />
      )}
    </div>
  );
}

function OverviewTab({ job }: { job: JobDetail }) {
  const [editing, setEditing] = useState(false);
  const queryClient = useQueryClient();
  if (editing)
    return (
      <>
        <button onClick={() => setEditing(false)}>Cancelar edição</button>
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
    <div className="bg-surface border border-line rounded-lg p-6 space-y-4">
      <button onClick={() => setEditing(true)} className="text-brand">
        Editar vaga
      </button>
      <p>Versão dos critérios: {job.criteria_version}</p>
      <div>
        <h3 className="text-sm text-ink-soft mb-1">Descrição</h3>
        <p className="text-ink whitespace-pre-wrap">{job.description}</p>
      </div>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-ink-soft">Experiência mínima:</span>{" "}
          {job.min_experience_years} ano(s)
        </div>
        <div>
          <span className="text-ink-soft">Formação:</span>{" "}
          {job.education_level ?? "Não especificada"}
        </div>
      </div>
    </div>
  );
}

function RequirementsTab({ job, jobId }: { job: JobDetail; jobId: string }) {
  const queryClient = useQueryClient();
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
    mutationFn: (requirementId: number) =>
      api.delete(`/requirements/${requirementId}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });

  const totalWeight = job.requirements.reduce((sum, r) => sum + r.weight, 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-ink-soft">
          Soma dos pesos:{" "}
          <span
            className={
              Math.abs(totalWeight - 1) > 0.01
                ? "text-warn font-medium"
                : "text-ink"
            }
          >
            {(totalWeight * 100).toFixed(0)}%
          </span>
          {Math.abs(totalWeight - 1) > 0.01 && " — o ideal é somar 100%"}
        </p>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="text-sm text-brand hover:text-brand-dark font-medium"
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
          className="bg-surface border border-line rounded-lg p-4 mb-4 grid grid-cols-4 gap-3 items-end"
        >
          <label className="col-span-2 text-sm">
            <span className="block text-ink-soft mb-1">Nome</span>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full rounded-sm border border-line px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm">
            <span className="block text-ink-soft mb-1">Categoria</span>
            <select
              value={form.category}
              onChange={(e) =>
                setForm({
                  ...form,
                  category: e.target.value as RequirementCategory,
                })
              }
              className="w-full rounded-sm border border-line px-3 py-2 text-sm"
            >
              {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="block text-ink-soft mb-1">Peso (%)</span>
            <input
              type="number"
              min={0}
              max={100}
              value={Math.round(form.weight * 100)}
              onChange={(e) =>
                setForm({ ...form, weight: Number(e.target.value) / 100 })
              }
              className="w-full rounded-sm border border-line px-3 py-2 text-sm"
            />
          </label>
          <label className="col-span-3 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.is_mandatory}
              onChange={(e) =>
                setForm({ ...form, is_mandatory: e.target.checked })
              }
            />
            <span className="text-ink-soft">Obrigatório</span>
          </label>
          <label className="col-span-3">
            Descrição
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
            />
          </label>
          <label>
            Nível esperado
            <select
              value={form.expected_level}
              onChange={(e) =>
                setForm({ ...form, expected_level: e.target.value })
              }
            >
              <option value="basic">Básico</option>
              <option value="intermediate">Intermédio</option>
              <option value="advanced">Avançado</option>
              <option value="expert">Especialista</option>
            </select>
          </label>
          <button
            type="submit"
            className="rounded-sm bg-brand text-white px-4 py-2 text-sm font-medium hover:bg-brand-dark"
          >
            Guardar requisito
          </button>
        </form>
      )}

      <div className="bg-surface border border-line rounded-lg divide-y divide-line">
        {totalWeight <= 0 && (
          <p role="alert">
            Defina pelo menos um peso superior a zero para analisar CVs.
          </p>
        )}
        {addMutation.isError && (
          <p role="alert">{apiErrorMessage(addMutation.error)}</p>
        )}
        {deleteMutation.isError && (
          <p role="alert">{apiErrorMessage(deleteMutation.error)}</p>
        )}
        {job.requirements.length === 0 && (
          <p className="px-5 py-8 text-center text-ink-faint text-sm">
            Ainda não há requisitos. Adicione pelo menos um antes de publicar a
            vaga.
          </p>
        )}
        {job.requirements.map((req: JobRequirement) => (
          <div
            key={req.id}
            className="flex items-center justify-between px-5 py-3"
          >
            <div>
              <span className="text-ink">{req.name}</span>
              <span className="text-ink-faint text-sm ml-2">
                {CATEGORY_LABELS[req.category]}
              </span>
              {req.is_mandatory && (
                <span className="ml-2 text-xs rounded-sm bg-danger-soft text-danger px-1.5 py-0.5">
                  Obrigatório
                </span>
              )}
            </div>
            <div className="flex items-center gap-4">
              <button
                className="text-brand"
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
              <span className="text-sm text-ink-soft">
                {(req.weight * 100).toFixed(0)}%
              </span>
              <button
                onClick={() => deleteMutation.mutate(req.id)}
                className="text-sm text-ink-faint hover:text-danger"
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

function CandidatesTab({ jobId }: { jobId: string }) {
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [pendingAnalysisIds, setPendingAnalysisIds] = useState<number[]>([]);

  const { data: applications, error: candidatesError } = useQuery({
    queryKey: ["job-candidates", jobId],
    queryFn: async () =>
      (await api.get<ApplicationDetail[]>(`/jobs/${jobId}/candidates`)).data,
    refetchInterval: query => query.state.data?.some(app => ["queued", "running"].includes(app.analysis_status)) ? 1500 : false,
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

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploadError(null);
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("candidate_name", candidateName);
      formData.append("candidate_email", candidateEmail);
      formData.append("file", file);
      await api.post(`/jobs/${jobId}/cvs`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      queryClient.invalidateQueries({ queryKey: ["job-candidates", jobId] });
      setCandidateName("");
      setCandidateEmail("");
      setFile(null);
      setUploadOpen(false);
    } catch (err) {
      setUploadError(apiErrorMessage(err, "Não foi possível carregar o CV."));
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setUploadOpen((v) => !v)}
          className="text-sm text-brand hover:text-brand-dark font-medium"
        >
          {uploadOpen ? "Cancelar" : "+ Carregar CV"}
        </button>
      </div>

      {uploadOpen && (
        <form
          onSubmit={handleUpload}
          className="bg-surface border border-line rounded-lg p-4 mb-4 grid grid-cols-3 gap-3 items-end"
        >
          <label className="text-sm">
            <span className="block text-ink-soft mb-1">Nome do candidato</span>
            <input
              required
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              className="w-full rounded-sm border border-line px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm">
            <span className="block text-ink-soft mb-1">E-mail</span>
            <input
              required
              type="email"
              value={candidateEmail}
              onChange={(e) => setCandidateEmail(e.target.value)}
              className="w-full rounded-sm border border-line px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm">
            <span className="block text-ink-soft mb-1">
              Ficheiro (PDF ou DOCX)
            </span>
            <input
              required
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm"
            />
          </label>
          {uploadError && (
            <p className="col-span-3 text-sm text-danger bg-danger-soft rounded-sm px-3 py-2">
              {uploadError}
            </p>
          )}
          <button
            type="submit"
            disabled={isUploading}
            className="rounded-sm bg-brand text-white px-4 py-2 text-sm font-medium hover:bg-brand-dark disabled:opacity-60"
          >
            {isUploading ? "A carregar..." : "Carregar"}
          </button>
        </form>
      )}

      <div className="bg-surface border border-line rounded-lg divide-y divide-line">
        {applications?.length === 0 && (
          <p className="px-5 py-8 text-center text-ink-faint text-sm">
            Ainda não há candidaturas para esta vaga.
          </p>
        )}
        {(candidatesError || analyzeMutation.isError) && <p role="alert">{apiErrorMessage(candidatesError || analyzeMutation.error)}</p>}
        {applications?.map((app) => (
          <div
            key={app.id}
            className="flex items-center justify-between px-5 py-3"
          >
            <div>
              <Link
                to={`/jobs/${jobId}/applications/${app.id}`}
                className="text-ink hover:text-brand font-medium"
              >
                {app.candidate.name}
              </Link>
              <p className="text-sm text-ink-faint">{app.candidate.email}</p>
            </div>
            <div className="flex items-center gap-3">
              <AnalysisStatusBadge value={pendingAnalysisIds.includes(app.latest_resume_id ?? -1) ? {...app, analysis_status: "queued"} : app} />
              {app.score !== null && (
                <span className="font-display text-lg text-ink">
                  {app.score.toFixed(0)}%
                </span>
              )}
              {analysisPresentation(app).action === "view" ? (
                <Link to={`/jobs/${jobId}/applications/${app.id}`} className="text-sm text-brand">Ver análise</Link>
              ) : analysisPresentation(app).action !== "busy" && (
                <button
                  onClick={() =>
                    app.latest_resume_id && analyzeMutation.mutate(app.latest_resume_id)
                  }
                  disabled={
                    analyzeMutation.isPending ||
                    !app.latest_resume_id || pendingAnalysisIds.includes(app.latest_resume_id)
                  }
                  className="text-sm text-brand hover:text-brand-dark font-medium disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {pendingAnalysisIds.includes(app.latest_resume_id ?? -1)
                    ? "Em fila..."
                    : analysisPresentation(app).actionLabel}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

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
      <div className="flex gap-2 mb-4 flex-wrap">
        {FILTERS.map(([value, label]) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`text-sm rounded-sm px-3 py-1.5 border transition-colors ${
              filter === value
                ? "border-brand bg-brand-soft text-brand-dark"
                : "border-line text-ink-soft hover:bg-canvas"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="bg-surface border border-line rounded-lg divide-y divide-line">
        {rankingError && <p role="alert">{apiErrorMessage(rankingError)}</p>}
        {ranking?.length === 0 && (
          <p className="px-5 py-8 text-center text-ink-faint text-sm">
            Nenhum candidato nesta categoria.
          </p>
        )}
        {ranking?.map((item, index) => (
          <Link
            key={item.application_id}
            to={`/jobs/${jobId}/applications/${item.application_id}`}
            className="flex items-center justify-between px-5 py-3 hover:bg-canvas transition-colors"
          >
            <div className="flex items-center gap-4">
              <span className="text-ink-faint text-sm w-5">{index + 1}.</span>
              <div>
                <p className="text-ink font-medium">{item.candidate_name}</p>
                <p className="text-sm text-ink-faint">{item.candidate_email}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <AnalysisStatusBadge value={item} />
              <span className="font-display text-lg text-ink w-14 text-right">
                {item.score !== null ? `${item.score.toFixed(0)}%` : "—"}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
