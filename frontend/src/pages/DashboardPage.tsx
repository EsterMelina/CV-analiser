import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";

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

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-surface border border-line rounded-lg px-5 py-4">
      <p className="font-display text-3xl text-ink">{value}</p>
      <p className="text-sm text-ink-soft mt-1">{label}</p>
    </div>
  );
}

export function DashboardPage() {
  const { data: summary } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: async () => (await api.get<Summary>("/dashboard/summary")).data,
  });

  const { data: byJob } = useQuery({
    queryKey: ["dashboard-by-job"],
    queryFn: async () => (await api.get<JobApplicationCount[]>("/dashboard/applications-by-job")).data,
  });

  return (
    <div>
      <h1 className="font-display text-2xl text-ink mb-1">Painel</h1>
      <p className="text-ink-soft mb-6">Visão geral da triagem de candidatos.</p>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MetricCard label="Vagas ativas" value={summary.active_jobs} />
          <MetricCard label="Vagas encerradas" value={summary.closed_jobs} />
          <MetricCard label="Candidatos" value={summary.total_candidates} />
          <MetricCard label="Candidaturas" value={summary.total_applications} />
          <MetricCard label="CVs analisados" value={summary.analyzed_applications} />
          <MetricCard label="Recomendados" value={summary.recommended_applications} />
          <MetricCard label="Em entrevista" value={summary.interview_selected_applications} />
          <MetricCard label="Por avaliar" value={summary.pending_evaluation_applications} />
        </div>
      )}

      <div className="bg-surface border border-line rounded-lg">
        <div className="px-5 py-4 border-b border-line">
          <h2 className="font-medium text-ink">Candidatos por vaga</h2>
        </div>
        {byJob && byJob.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-soft border-b border-line">
                <th className="px-5 py-2 font-normal">Vaga</th>
                <th className="px-5 py-2 font-normal">Candidaturas</th>
                <th className="px-5 py-2 font-normal">Recomendados</th>
              </tr>
            </thead>
            <tbody>
              {byJob.map((row) => (
                <tr key={row.job_id} className="border-b border-line last:border-0">
                  <td className="px-5 py-3">
                    <Link to={`/jobs/${row.job_id}`} className="text-brand hover:text-brand-dark">
                      {row.job_title}
                    </Link>
                    <span className="text-ink-faint ml-2">{row.job_code}</span>
                  </td>
                  <td className="px-5 py-3">{row.total_applications}</td>
                  <td className="px-5 py-3">{row.recommended}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="px-5 py-8 text-center text-ink-faint text-sm">
            Ainda não há vagas com candidaturas.
          </p>
        )}
      </div>
    </div>
  );
}
