import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import type { JobListItem, JobStatus } from "@/types";
import "./JobsList.css";

const STATUS_LABELS: Record<JobStatus, string> = {
  draft: "Rascunho",
  published: "Publicada",
  closed: "Encerrada",
  archived: "Arquivada",
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
    <div className="jobs-page">
      <div className="jobs-page__header">
        <div>
          <h1 className="jobs-page__title">Vagas</h1>
          <p className="jobs-page__subtitle">
            Crie vagas e acompanhe as candidaturas recebidas.
          </p>
        </div>
        <Link to="/jobs/new" className="btn-primary-solid">
          Nova vaga
        </Link>
      </div>

      <div className="jobs-page__filters">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Pesquisar por título ou código..."
          className="jobs-page__search"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as JobStatus | "")}
          className="jobs-page__select"
        >
          <option value="">Todos os estados</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div className="jobs-list">
        {isLoading && <p className="jobs-list__state">A carregar...</p>}

        {!isLoading && jobs?.length === 0 && (
          <p className="jobs-list__state">Nenhuma vaga encontrada.</p>
        )}

        {jobs?.map((job) => (
          <Link key={job.id} to={`/jobs/${job.id}`} className="jobs-list__item">
            <div className="jobs-list__info">
              <p className="jobs-list__title">{job.title}</p>
              <p className="jobs-list__meta">
                {job.code}
                {job.department ? ` · ${job.department}` : ""}
                {job.location ? ` · ${job.location}` : ""}
              </p>
            </div>
            <span className={`jobs-list__status jobs-list__status--${job.status}`}>
              {STATUS_LABELS[job.status]}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}