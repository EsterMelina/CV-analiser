import { useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { api, apiErrorMessage } from "@/lib/api";
import type { JobModality, JobType, JobDetail } from "@/types";

export function JobCreatePage({ job, onSaved }: { job?: JobDetail; onSaved?: () => void }) {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [form, setForm] = useState({
    title: job?.title ?? "", code: job?.code ?? "", description: job?.description ?? "", department: job?.department ?? "", location: job?.location ?? "",
    job_type: job?.job_type ?? "full_time" as JobType, modality: job?.modality ?? "on_site" as JobModality,
    min_experience_years: job?.min_experience_years ?? 0, education_level: job?.education_level ?? "",
  });

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const { data } = job ? await api.put(`/jobs/${job.id}`, form) : await api.post("/jobs", form);
      if (onSaved) onSaved(); else navigate(`/jobs/${data.id}`);
    } catch (err) {
      setError(apiErrorMessage(err, "Não foi possível criar a vaga."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-2xl text-ink mb-1">{job ? "Editar vaga" : "Nova vaga"}</h1>
      <p className="text-ink-soft mb-6">Depois de criada, adicione os requisitos antes de publicar.</p>

      <form onSubmit={handleSubmit} className="bg-surface border border-line rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Título" required>
            <input required value={form.title} onChange={(e) => update("title", e.target.value)} className={inputClass} />
          </Field>
          <Field label="Código da vaga" required>
            <input required value={form.code} onChange={(e) => update("code", e.target.value)} placeholder="VAG-2026-001" className={inputClass} />
          </Field>
        </div>

        <Field label="Descrição" required>
          <textarea required rows={4} value={form.description} onChange={(e) => update("description", e.target.value)} className={inputClass} />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Departamento">
            <input value={form.department} onChange={(e) => update("department", e.target.value)} className={inputClass} />
          </Field>
          <Field label="Localização">
            <input value={form.location} onChange={(e) => update("location", e.target.value)} className={inputClass} />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Tipo de trabalho">
            <select value={form.job_type} onChange={(e) => update("job_type", e.target.value as JobType)} className={inputClass}>
              <option value="full_time">Tempo inteiro</option>
              <option value="part_time">Meio período</option>
              <option value="internship">Estágio</option>
              <option value="contract">Contrato</option>
              <option value="temporary">Temporário</option>
            </select>
          </Field>
          <Field label="Modalidade">
            <select value={form.modality} onChange={(e) => update("modality", e.target.value as JobModality)} className={inputClass}>
              <option value="on_site">Presencial</option>
              <option value="remote">Remoto</option>
              <option value="hybrid">Híbrido</option>
            </select>
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Experiência mínima (anos)">
            <input
              type="number" min={0} value={form.min_experience_years}
              onChange={(e) => update("min_experience_years", Number(e.target.value))}
              className={inputClass}
            />
          </Field>
          <Field label="Formação académica">
            <input value={form.education_level} onChange={(e) => update("education_level", e.target.value)} className={inputClass} />
            <small>Campo descritivo. Para avaliar formação, acrescente um requisito da categoria Formação com peso e obrigatoriedade.</small>
          </Field>
        </div>

        {error && <p className="text-sm text-danger bg-danger-soft rounded-sm px-3 py-2">{error}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-sm bg-brand text-white px-4 py-2 text-sm font-medium hover:bg-brand-dark transition-colors disabled:opacity-60"
          >
            {isSubmitting ? "A guardar..." : job ? "Guardar alterações" : "Criar vaga"}
          </button>
        </div>
      </form>
    </div>
  );
}

const inputClass = "w-full rounded-sm border border-line px-3 py-2 text-sm focus:border-brand";

function Field({ label, required, children }: { label: string; required?: boolean; children: ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm text-ink-soft mb-1">
        {label}{required && <span className="text-danger"> *</span>}
      </span>
      {children}
    </label>
  );
}
