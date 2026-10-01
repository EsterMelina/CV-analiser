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

  const { data: jobs, isLoading, isError, refetch } = useQuery({
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
        {isLoading && (
          <div className="jobs-list__loading" role="status" aria-label="A carregar vagas">
            {Array.from({ length: 5 }, (_, index) => (
              <div className="jobs-list__loading-item" key={index}>
                <span className="jobs-list__skeleton jobs-list__skeleton--title" />
                <span className="jobs-list__skeleton jobs-list__skeleton--meta" />
                <span className="jobs-list__skeleton jobs-list__skeleton--status" />
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="jobs-list__state jobs-list__state--error" role="alert">
            <span className="material-symbols-outlined" aria-hidden="true">cloud_off</span>
            <p>Não foi possível carregar as vagas.</p>
            <button type="button" onClick={() => void refetch()}>Tentar novamente</button>
          </div>
        )}

        {!isLoading && !isError && jobs?.length === 0 && (
          <div className="jobs-list__state">
            <span className="material-symbols-outlined" aria-hidden="true">search_off</span>
            <p>Nenhuma vaga encontrada com estes filtros.</p>
          </div>
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