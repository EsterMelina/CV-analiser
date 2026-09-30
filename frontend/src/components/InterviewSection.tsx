import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiErrorMessage } from "@/lib/api";
import type { Interview } from "@/types";
import "./InterviewSection.css";

export function InterviewSection({ applicationId }: { applicationId: string }) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [scheduledAt, setScheduledAt] = useState("");
  const [interviewers, setInterviewers] = useState("");

  const { data: interviews, error: interviewsError } = useQuery({
    queryKey: ["interviews", applicationId],
    queryFn: async () =>
      (await api.get<Interview[]>(`/applications/${applicationId}/interviews`)).data,
  });

  const scheduleMutation = useMutation({
    mutationFn: () =>
      api.post(`/applications/${applicationId}/interview`, {
        scheduled_at: scheduledAt,
        interviewers,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      setShowForm(false);
      setScheduledAt("");
      setInterviewers("");
    },
  });

  const resultMutation = useMutation({
    mutationFn: ({ id, result }: { id: number; result: string }) =>
      api.patch(`/interviews/${id}/result`, { result }),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  return (
    <div className="iv">
      <div className="iv__header">
        <h2 className="iv__title">Entrevistas</h2>
        <button
          className="iv__toggle"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? "Cancelar" : "+ Agendar entrevista"}
        </button>
      </div>

      {(interviewsError || scheduleMutation.error || resultMutation.error) && (
        <p role="alert" className="iv__alert">
          {apiErrorMessage(interviewsError || scheduleMutation.error || resultMutation.error)}
        </p>
      )}

      {showForm && (
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            scheduleMutation.mutate();
          }}
          className="iv__form"
        >
          <label className="iv__field">
            <span>Data e hora</span>
            <input
              required
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="iv__input"
            />
          </label>
          <label className="iv__field">
            <span>Entrevistadores</span>
            <input
              value={interviewers}
              onChange={(e) => setInterviewers(e.target.value)}
              className="iv__input"
            />
          </label>
          <button
            type="submit"
            disabled={scheduleMutation.isPending}
            className="iv__submit"
          >
            Agendar
          </button>
        </form>
      )}

      {interviews?.length === 0 && (
        <p className="iv__empty">Nenhuma entrevista agendada.</p>
      )}

      <div className="iv__list">
        {interviews?.map((interview) => (
          <div key={interview.id} className="iv__item">
            <span className="iv__item-date">
              {new Date(interview.scheduled_at).toLocaleString("pt-PT")}
            </span>
            <select
              value={interview.result}
              disabled={resultMutation.isPending}
              onChange={(e) =>
                resultMutation.mutate({
                  id: interview.id,
                  result: e.target.value,
                })
              }
              className="iv__select"
            >
              <option value="scheduled">Agendada</option>
              <option value="completed">Realizada</option>
              <option value="cancelled">Cancelada</option>
              <option value="no_show">Não compareceu</option>
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}