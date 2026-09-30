import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import type { JobListItem, JobStatus } from "@/types";

const STATUS_LABELS: Record<JobStatus, string> = {
  draft: "Rascunho",
  published: "Publicada",
  closed: "Encerrada",
  archived: "Arquivada",
};

const STATUS_STYLES: Record<JobStatus, string> = {
  draft: "bg-ink/5 text-ink-soft",
  published: "bg-brand-soft text-brand-dark",
  closed: "bg-warn-soft text-warn",
  archived: "bg-ink/5 text-ink-faint",
};

export function JobsListPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<JobStatus | "">("");

  const { data: jobs, isLoading } = useQuery({
    queryKey: ["jobs", search, statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      return (await api.get<JobListItem[]>("/jobs", { params })).data;
    },
  });

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl text-ink mb-1">Vagas</h1>
          <p className="text-ink-soft">Crie vagas e acompanhe as candidaturas recebidas.</p>
        </div>
        <Link
          to="/jobs/new"
          className="rounded-sm bg-brand text-white px-4 py-2 text-sm font-medium hover:bg-brand-dark transition-colors"
        >
          Nova vaga
        </Link>
      </div>

      <div className="flex gap-3 mb-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Pesquisar por título ou código..."
          className="flex-1 rounded-sm border border-line px-3 py-2 text-sm focus:border-brand"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as JobStatus | "")}
          className="rounded-sm border border-line px-3 py-2 text-sm focus:border-brand"
        >
          <option value="">Todos os estados</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      <div className="bg-surface border border-line rounded-lg divide-y divide-line">
        {isLoading && <p className="px-5 py-8 text-center text-ink-faint text-sm">A carregar...</p>}
        {!isLoading && jobs?.length === 0 && (
          <p className="px-5 py-8 text-center text-ink-faint text-sm">Nenhuma vaga encontrada.</p>
        )}
        {jobs?.map((job) => (
          <Link
            key={job.id}
            to={`/jobs/${job.id}`}
            className="flex items-center justify-between px-5 py-4 hover:bg-canvas transition-colors"
          >
            <div>
              <p className="text-ink font-medium">{job.title}</p>
              <p className="text-sm text-ink-faint">
                {job.code}{job.department ? ` · ${job.department}` : ""}{job.location ? ` · ${job.location}` : ""}
              </p>
            </div>
            <span className={`text-sm rounded-sm px-2 py-0.5 ${STATUS_STYLES[job.status]}`}>
              {STATUS_LABELS[job.status]}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
