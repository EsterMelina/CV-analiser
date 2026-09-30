import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiErrorMessage } from "@/lib/api";
import type { EmailAccountRead } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  connected: "bg-brand-soft text-brand-dark",
  error: "bg-danger-soft text-danger",
  disconnected: "bg-ink/5 text-ink-soft",
};

const STATUS_LABELS: Record<string, string> = {
  connected: "Conectado", error: "Erro", disconnected: "Desconectado",
};

export function EmailSettingsPage() {
  const queryClient = useQueryClient();
  const [provider, setProvider] = useState<"imap" | "gmail" | "outlook">("imap");
  const [form, setForm] = useState({
    email_address: "", imap_host: "", imap_port: 993, imap_password: "", oauth_access_token: "",
  });
  const [connectError, setConnectError] = useState<string | null>(null);

  const { data: account, error } = useQuery({
    queryKey: ["email-status"],
    queryFn: async () => (await api.get<EmailAccountRead>("/email/status")).data,
    retry: false,
  });
  const notConnected = !!(error as any)?.response && (error as any).response.status === 404;

  const connectMutation = useMutation({
    mutationFn: () => api.post("/email/connect", {
      email_address: form.email_address,
      provider,
      ...(provider === "imap"
        ? { imap_host: form.imap_host, imap_port: form.imap_port, imap_password: form.imap_password }
        : { oauth_access_token: form.oauth_access_token }),
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email-status"] }),
    onError: (err) => setConnectError(apiErrorMessage(err, "Não foi possível ligar a conta.")),
  });

  const syncMutation = useMutation({
    mutationFn: () => api.post("/email/sync"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email-status"] }),
  });

  const disconnectMutation = useMutation({
    mutationFn: () => api.delete("/email/disconnect"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["email-status"] }),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setConnectError(null);
    connectMutation.mutate();
  }

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-2xl text-ink mb-1">Integração de e-mail</h1>
      <p className="text-ink-soft mb-6">
        Ligue a caixa de entrada usada para receber candidaturas (ex: recrutamento@empresa.co.mz).
      </p>

      {account && account.status !== "disconnected" && (
        <div className="bg-surface border border-line rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-ink font-medium">{account.email_address}</p>
              <p className="text-sm text-ink-faint capitalize">{account.provider}</p>
            </div>
            <span className={`text-sm rounded-sm px-2 py-0.5 ${STATUS_STYLES[account.status]}`}>
              {STATUS_LABELS[account.status]}
            </span>
          </div>

          {account.last_sync_error && (
            <p className="text-sm text-danger bg-danger-soft rounded-sm px-3 py-2 mb-4">{account.last_sync_error}</p>
          )}

          <div className="grid grid-cols-4 gap-4 text-sm mb-4">
            <div><p className="font-display text-xl text-ink">{account.messages_processed_count}</p><p className="text-ink-faint">Mensagens</p></div>
            <div><p className="font-display text-xl text-ink">{account.cvs_found_count}</p><p className="text-ink-faint">CVs encontrados</p></div>
            <div><p className="font-display text-xl text-ink">{account.cvs_analyzed_count}</p><p className="text-ink-faint">CVs analisados</p></div>
            <div><p className="font-display text-xl text-ink">{account.errors_count}</p><p className="text-ink-faint">Erros</p></div>
          </div>

          <p className="text-sm text-ink-faint mb-4">
            Última sincronização: {account.last_sync_at ? new Date(account.last_sync_at).toLocaleString("pt-PT") : "nunca"}
          </p>

          <div className="flex gap-3">
            <button
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
              className="rounded-sm bg-brand text-white px-4 py-2 text-sm font-medium hover:bg-brand-dark disabled:opacity-60"
            >
              {syncMutation.isPending ? "A sincronizar..." : "Sincronizar agora"}
            </button>
            <button
              onClick={() => disconnectMutation.mutate()}
              className="rounded-sm border border-line px-4 py-2 text-sm font-medium text-ink-soft hover:bg-canvas"
            >
              Desligar
            </button>
          </div>
        </div>
      )}

      {(notConnected || account?.status === "disconnected") && (
        <form onSubmit={handleSubmit} className="bg-surface border border-line rounded-lg p-6 space-y-4">
          <label className="block text-sm">
            <span className="block text-ink-soft mb-1">E-mail da empresa</span>
            <input
              required type="email" value={form.email_address}
              onChange={(e) => setForm({ ...form, email_address: e.target.value })}
              placeholder="recrutamento@empresa.co.mz"
              className="w-full rounded-sm border border-line px-3 py-2 text-sm"
            />
          </label>

          <label className="block text-sm">
            <span className="block text-ink-soft mb-1">Provedor</span>
            <select value={provider} onChange={(e) => setProvider(e.target.value as typeof provider)} className="w-full rounded-sm border border-line px-3 py-2 text-sm">
              <option value="imap">IMAP</option>
              <option value="gmail">Gmail / Google Workspace</option>
              <option value="outlook">Microsoft 365 / Outlook</option>
            </select>
          </label>

          {provider === "imap" ? (
            <>
              <label className="block text-sm">
                <span className="block text-ink-soft mb-1">Servidor IMAP</span>
                <input
                  required value={form.imap_host} onChange={(e) => setForm({ ...form, imap_host: e.target.value })}
                  placeholder="imap.empresa.co.mz" className="w-full rounded-sm border border-line px-3 py-2 text-sm"
                />
              </label>
              <label className="block text-sm">
                <span className="block text-ink-soft mb-1">Palavra-passe</span>
                <input
                  required type="password" value={form.imap_password}
                  onChange={(e) => setForm({ ...form, imap_password: e.target.value })}
                  className="w-full rounded-sm border border-line px-3 py-2 text-sm"
                />
              </label>
            </>
          ) : (
            <p className="text-sm text-ink-soft bg-canvas rounded-sm px-3 py-2">
              A ligação a {provider === "gmail" ? "Gmail" : "Outlook"} exige que a empresa registe primeiro uma
              aplicação OAuth ({provider === "gmail" ? "Google Cloud Console" : "Azure AD"}) — sem isso, não há um
              token de acesso válido para colar aqui. Peça à sua equipa de TI para tratar disso; entretanto, o IMAP
              é a via mais rápida para começar a receber candidaturas por e-mail.
            </p>
          )}

          {connectError && <p className="text-sm text-danger bg-danger-soft rounded-sm px-3 py-2">{connectError}</p>}

          {provider === "imap" && (
            <button
              type="submit"
              disabled={connectMutation.isPending}
              className="rounded-sm bg-brand text-white px-4 py-2 text-sm font-medium hover:bg-brand-dark disabled:opacity-60"
            >
              {connectMutation.isPending ? "A ligar..." : "Ligar conta"}
            </button>
          )}
        </form>
      )}
    </div>
  );
}
