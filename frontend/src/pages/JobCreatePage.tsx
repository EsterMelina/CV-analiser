import { useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { api, apiErrorMessage } from "@/lib/api";
import type { JobModality, JobType, JobDetail } from "@/types";
import "./JobCreate.css";

export function JobCreatePage({
  job,
  onSaved,
}: {
  job?: JobDetail;
  onSaved?: () => void;
}) {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [form, setForm] = useState({
    title: job?.title ?? "",
    code: job?.code ?? "",
    description: job?.description ?? "",
    department: job?.department ?? "",
    location: job?.location ?? "",
    job_type: job?.job_type ?? ("full_time" as JobType),
    modality: job?.modality ?? ("on_site" as JobModality),
    min_experience_years: job?.min_experience_years ?? 0,
    education_level: job?.education_level ?? "",
  });

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const { data } = job
        ? await api.put(`/jobs/${job.id}`, form)
        : await api.post("/jobs", form);
      if (onSaved) onSaved();
      else navigate(`/jobs/${data.id}`);
    } catch (err) {
      setError(apiErrorMessage(err, "Não foi possível criar a vaga."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="job-create">
      <h1 className="job-create__title">{job ? "Editar vaga" : "Nova vaga"}</h1>
      <p className="job-create__subtitle">
        Depois de criada, adicione os requisitos antes de publicar.
      </p>

      <form onSubmit={handleSubmit} className="job-create__form">
        <div className="job-create__grid">
          <Field label="Título" required>
            <input
              required
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              className="job-input"
            />
          </Field>
          <Field label="Código da vaga" required>
            <input
              required
              value={form.code}
              onChange={(e) => update("code", e.target.value)}
              placeholder="VAG-2026-001"
              className="job-input"
            />
          </Field>
        </div>

        <Field label="Descrição" required>
          <textarea
            required
            rows={4}
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
            className="job-textarea"
          />
        </Field>

        <div className="job-create__grid">
          <Field label="Departamento">
            <input
              value={form.department}
              onChange={(e) => update("department", e.target.value)}
              className="job-input"
            />
          </Field>
          <Field label="Localização">
            <input
              value={form.location}
              onChange={(e) => update("location", e.target.value)}
              className="job-input"
            />
          </Field>
        </div>

        <div className="job-create__grid">
          <Field label="Tipo de trabalho">
            <select
              value={form.job_type}
              onChange={(e) => update("job_type", e.target.value as JobType)}
              className="job-select"
            >
              <option value="full_time">Tempo inteiro</option>
              <option value="part_time">Meio período</option>
              <option value="internship">Estágio</option>
              <option value="contract">Contrato</option>
              <option value="temporary">Temporário</option>
            </select>
          </Field>
          <Field label="Modalidade">
            <select
              value={form.modality}
              onChange={(e) => update("modality", e.target.value as JobModality)}
              className="job-select"
            >
              <option value="on_site">Presencial</option>
              <option value="remote">Remoto</option>
              <option value="hybrid">Híbrido</option>
            </select>
          </Field>
        </div>

        <div className="job-create__grid">
          <Field label="Experiência mínima (anos)">
            <input
              type="number"
              min={0}
              value={form.min_experience_years}
              onChange={(e) => update("min_experience_years", Number(e.target.value))}
              className="job-input"
            />
          </Field>
          <Field label="Formação académica">
            <input
              value={form.education_level}
              onChange={(e) => update("education_level", e.target.value)}
              className="job-input"
            />
            <small className="job-field__hint">
              Campo descritivo. Para avaliar formação, acrescente um requisito da categoria
              Formação com peso e obrigatoriedade.
            </small>
          </Field>
        </div>

        {error && <p className="job-create__error" role="alert">{error}</p>}

        <div className="job-create__actions">
          <button
            type="submit"
            disabled={isSubmitting}
            className="job-create__submit"
          >
            {isSubmitting && (
              <span className="material-symbols-outlined job-create__spinner" aria-hidden="true">
                progress_activity
              </span>
            )}
            {isSubmitting ? "A guardar..." : job ? "Guardar alterações" : "Criar vaga"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label className="job-field">
      <span className="job-field__label">
        {label}
        {required && <span className="job-field__required"> *</span>}
      </span>
      {children}
    </label>
  );
}