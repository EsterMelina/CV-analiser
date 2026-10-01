import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import "./Dashboard.css";

/* ==================== Types ==================== */

interface Summary {
  total_jobs: number;
  active_jobs: number;
  closed_jobs: number;
  total_candidates: number;
  total_applications: number;
  analyzed_applications: number;
  recommended_applications: number;
  interview_selected_applications: number;
  pending_evaluation_applications: number;
}

interface JobApplicationCount {
  job_id: number;
  job_title: string;
  job_code: string;
  total_applications: number;
  recommended: number;
}

/* ==================== Metric Card ==================== */

type Tone = "info" | "positive" | "warning" | "default";

interface MetricCardProps {
  icon: string;
  label: string;
  value: number;
  tone?: Tone;
}

function MetricCard({ icon, label, value, tone = "default" }: MetricCardProps) {
  return (
    <div className={`sir-metric sir-metric--${tone}`}>
      <div className="sir-metric__top">
        <div className="sir-metric__icon">{icon}</div>
      </div>
      <div className="sir-metric__body">
        <div className="sir-metric__value">{value.toLocaleString("pt-PT")}</div>
        <div className="sir-metric__label">{label}</div>
      </div>
    </div>
  );
}

/* ==================== Page ==================== */

export function DashboardPage() {
  const {
    data: summary,
    isLoading: isSummaryLoading,
    isError: isSummaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: async () => (await api.get<Summary>("/dashboard/summary")).data,
  });

  const {
    data: byJob,
    isLoading: isByJobLoading,
    isError: isByJobError,
    refetch: refetchByJob,
  } = useQuery({
    queryKey: ["dashboard-by-job"],
    queryFn: async () =>
      (await api.get<JobApplicationCount[]>("/dashboard/applications-by-job")).data,
  });

  return (
    <div className="sir-dash">
      {/* ===== Header ===== */}
      <div className="sir-dash__header">
        <div>
          <span className="sir-dash__eyebrow">Visão geral</span>
          <h1 className="sir-dash__title">Painel</h1>
          <p className="sir-dash__subtitle">
            Acompanhe o ritmo das candidaturas e avance com os melhores perfis.
          </p>
        </div>
        <Link to="/jobs/new" className="sir-dash__primary-action">
          <span className="material-symbols-outlined" aria-hidden="true">add</span>
          Nova vaga
        </Link>
      </div>

      {/* ===== Métricas ===== */}
      {isSummaryLoading && (
        <div className="sir-dash__metrics" aria-label="A carregar indicadores" role="status">
          {Array.from({ length: 8 }, (_, index) => (
            <div className="sir-metric sir-metric--loading" key={index}>
              <span className="sir-skeleton sir-skeleton--icon" />
              <span className="sir-skeleton sir-skeleton--value" />
              <span className="sir-skeleton sir-skeleton--label" />
            </div>
          ))}
        </div>
      )}
      {isSummaryError && (
        <div className="sir-dash__alert" role="alert">
          <span className="material-symbols-outlined" aria-hidden="true">error</span>
          <span>Não foi possível carregar os indicadores.</span>
          <button type="button" onClick={() => void refetchSummary()}>Tentar novamente</button>
        </div>
      )}
      {summary && (
        <div className="sir-dash__metrics">
          <MetricCard icon="work"            label="Vagas ativas"     value={summary.active_jobs} tone="info" />
          <MetricCard icon="task_alt"        label="Vagas encerradas" value={summary.closed_jobs} />
          <MetricCard icon="group"           label="Candidatos"       value={summary.total_candidates} />
          <MetricCard icon="description"     label="Candidaturas"     value={summary.total_applications} />
          <MetricCard icon="fact_check"      label="CVs analisados"   value={summary.analyzed_applications} tone="info" />
          <MetricCard icon="thumb_up"        label="Recomendados"     value={summary.recommended_applications} tone="positive" />
          <MetricCard icon="event_available" label="Em entrevista"    value={summary.interview_selected_applications} tone="positive" />
          <MetricCard icon="pending"         label="Por avaliar"      value={summary.pending_evaluation_applications} tone="warning" />
        </div>
      )}

      {/* ===== Tabela ===== */}
      <div className="sir-card">
        <div className="sir-card__header">
          <div className="sir-card__title-wrap">
            <div className="sir-card__title-icon">view_list</div>
            <h2 className="sir-card__title">Candidatos por vaga</h2>
          </div>

          {byJob && byJob.length > 0 && (
            <span className="sir-card__count">
              {byJob.length} {byJob.length === 1 ? "vaga" : "vagas"}
            </span>
          )}
        </div>

        {isByJobLoading ? (
          <div className="sir-table__loading" aria-label="A carregar vagas" role="status">
            {Array.from({ length: 4 }, (_, index) => (
              <div className="sir-table__loading-row" key={index}>
                <span className="sir-skeleton sir-skeleton--job" />
                <span className="sir-skeleton sir-skeleton--number" />
                <span className="sir-skeleton sir-skeleton--number" />
                <span className="sir-skeleton sir-skeleton--action" />
              </div>
            ))}
          </div>
        ) : isByJobError ? (
          <div className="sir-empty sir-empty--error" role="alert">
            <span className="sir-empty__icon">error</span>
            <p className="sir-empty__text">Não foi possível carregar as candidaturas por vaga.</p>
            <button type="button" onClick={() => void refetchByJob()}>Tentar novamente</button>
          </div>
        ) : byJob && byJob.length > 0 ? (
          <div className="sir-table-wrap">
            <table className="sir-table">
              <thead>
                <tr>
                  <th>Vaga &amp; Código</th>
                  <th className="is-right">Candidaturas</th>
                  <th className="is-center">Recomendados</th>
                  <th className="is-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {byJob.map((row) => (
                  <tr key={row.job_id}>
                    <td>
                      <div className="sir-table__job">
                        <Link to={`/jobs/${row.job_id}`} className="sir-table__job-title">
                          {row.job_title}
                        </Link>
                        <span className="sir-table__job-code">{row.job_code}</span>
                      </div>
                    </td>

                    <td className="is-right">
                      <span className="sir-table__num">
                        {row.total_applications.toLocaleString("pt-PT")}
                      </span>
                    </td>

                    <td className="is-center">
                      {row.recommended > 0 ? (
                        <span className="sir-table__badge">
                          <span className="sir-table__badge-icon">verified</span>
                          <span>{row.recommended.toLocaleString("pt-PT")}</span>
                        </span>
                      ) : (
                        <span className="sir-table__zero">0</span>
                      )}
                    </td>

                    <td className="is-right">
                      <div className="sir-table__actions">
                        <Link to={`/jobs/${row.job_id}`} className="sir-table__btn">
                          Ver ranking
                        </Link>
                        <Link
                          to={`/jobs/${row.job_id}`}
                          aria-label={`Abrir vaga ${row.job_title}`}
                          className="sir-table__icon-btn"
                        >
                          <span className="sir-table__icon">chevron_right</span>
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="sir-empty">
            <span className="sir-empty__icon">inbox</span>
            <p className="sir-empty__text">Ainda não há vagas com candidaturas.</p>
            <Link to="/jobs" className="sir-empty__link">Explorar vagas</Link>
          </div>
        )}
      </div>
    </div>
  );
}