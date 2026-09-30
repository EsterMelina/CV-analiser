import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiErrorMessage } from "@/lib/api";
import type { Interview } from "@/types";

export function InterviewSection({ applicationId }: { applicationId: string }) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [scheduledAt, setScheduledAt] = useState("");
  const [interviewers, setInterviewers] = useState("");

  const { data: interviews, error: interviewsError } = useQuery({
    queryKey: ["interviews", applicationId],
    queryFn: async () =>
      (await api.get<Interview[]>(`/applications/${applicationId}/interviews`))
        .data,
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
    <div className="bg-surface border border-line rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-medium text-ink">Entrevistas</h2>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="text-sm text-brand hover:text-brand-dark font-medium"
        >
          {showForm ? "Cancelar" : "+ Agendar entrevista"}
        </button>
      </div>

      {(interviewsError || scheduleMutation.error || resultMutation.error) && (
        <p role="alert">{apiErrorMessage(interviewsError || scheduleMutation.error || resultMutation.error)}</p>
      )}
      {showForm && (
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            scheduleMutation.mutate();
          }}
          className="grid grid-cols-2 gap-3 mb-4"
        >
          <label className="text-sm">
            <span className="block text-ink-soft mb-1">Data e hora</span>
            <input
              required
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="w-full rounded-sm border border-line px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm">
            <span className="block text-ink-soft mb-1">Entrevistadores</span>
            <input
              value={interviewers}
              onChange={(e) => setInterviewers(e.target.value)}
              className="w-full rounded-sm border border-line px-3 py-2 text-sm"
            />
          </label>
          <button
            type="submit"
            disabled={scheduleMutation.isPending}
            className="col-span-2 rounded-sm bg-brand text-white px-4 py-2 text-sm font-medium hover:bg-brand-dark"
          >
            Agendar
          </button>
        </form>
      )}

      {interviews?.length === 0 && (
        <p className="text-sm text-ink-faint">Nenhuma entrevista agendada.</p>
      )}
      <div className="space-y-2">
        {interviews?.map((interview) => (
          <div
            key={interview.id}
            className="flex items-center justify-between text-sm border border-line rounded-sm px-3 py-2"
          >
            <span>
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
              className="rounded-sm border border-line px-2 py-1 text-sm"
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
