import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível iniciar sessão.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <p className="font-display text-3xl text-ink">Recrutamento</p>
          <p className="font-display text-3xl text-ink-soft -mt-1">Inteligente</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-surface border border-line rounded-lg p-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm text-ink-soft mb-1">E-mail</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-sm border border-line px-3 py-2 text-sm focus:border-brand"
              placeholder="recrutamento@empresa.co.mz"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm text-ink-soft mb-1">Palavra-passe</label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-sm border border-line px-3 py-2 text-sm focus:border-brand"
            />
          </div>

          {error && (
            <p className="text-sm text-danger bg-danger-soft rounded-sm px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-sm bg-brand text-white py-2 text-sm font-medium hover:bg-brand-dark transition-colors disabled:opacity-60"
          >
            {isSubmitting ? "A entrar..." : "Entrar"}
          </button>
        </form>

        <p className="text-xs text-ink-faint text-center mt-4">
          Dados de acesso de exemplo: recrutamento@techmoz.co.mz / Recruta@123
        </p>
      </div>
    </div>
  );
}
