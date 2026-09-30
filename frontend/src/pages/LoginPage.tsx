import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { SirLogo } from "@/components/SirLogo";
import { TechBackdrop } from "@/components/TechBackdrop";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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
    <div className="relative flex min-h-screen items-center justify-center bg-canvas px-4 py-10 text-ink">
      <TechBackdrop />

      <div className="relative z-10 w-full max-w-md">
        {/* Card vertical alto */}
        <form
          onSubmit={handleSubmit}
          className="glass-card flex flex-col gap-6 rounded-2xl border border-white/80 p-8 shadow-modal sm:p-10"
        >
          {/* Marca */}
          <div className="flex flex-col items-center text-center">
            <SirLogo size={48} markOnly className="mb-3" />
            <h1 className="text-xl font-bold tracking-tight text-ink">Entrar no SIR</h1>
            <p className="mt-1 text-xs text-ink-soft">
              Sistema Inteligente de Recrutamento
            </p>
          </div>

          {/* Campos */}
          <div className="space-y-5">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-ink-soft">
                E-mail
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nome@empresa.co.mz"
                className="custom-input block w-full rounded-lg border border-line-input bg-surface px-4 py-3 text-sm text-ink placeholder-ink-faint transition-colors focus:border-brand focus:outline-none"
              />
            </div>

            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label htmlFor="password" className="block text-xs font-medium text-ink-soft">
                  Palavra-passe
                </label>
                <a
                  href="#recuperar"
                  className="text-xs font-medium text-brand transition-colors hover:text-brand-dark hover:underline"
                >
                  Esqueceu-se?
                </a>
              </div>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="custom-input block w-full rounded-lg border border-line-input bg-surface px-4 py-3 pr-11 text-sm text-ink placeholder-ink-faint transition-colors focus:border-brand focus:outline-none"
                />
                <button
                  type="button"
                  aria-label="Alternar exibição de palavra-passe"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-ink-faint transition-colors hover:text-ink-soft"
                >
                  {showPassword ? (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" strokeLinecap="round" strokeLinejoin="round" />
                      <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <p
                role="alert"
                className="rounded-lg border border-danger-border bg-danger-soft px-3 py-2 text-xs text-danger-ink"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="h-12 w-full rounded-lg bg-brand text-sm font-semibold text-white shadow-md shadow-brand/25 transition-colors hover:bg-brand-dark active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "A autenticar…" : "Entrar"}
            </button>
          </div>

          {/* Divisor */}
          <div className="relative flex items-center">
            <span className="h-px flex-1 bg-line" />
            <span className="px-3 text-[10px] font-medium uppercase tracking-wider text-ink-faint">
              ou
            </span>
            <span className="h-px flex-1 bg-line" />
          </div>

          {/* Registo */}
          <div className="space-y-3 text-center">
            <p className="text-xs text-ink-soft">
              Não tens conta?
            </p>
            <a
              href="#registo"
              className="flex h-11 w-full items-center justify-center rounded-lg border border-brand/30 bg-ai-soft text-sm font-semibold text-brand transition-colors hover:bg-brand-soft hover:border-brand/50"
            >
              Criar conta
            </a>
          </div>

          {/* Credenciais demo */}
          <div className="rounded-lg border border-line bg-subtle/60 px-3 py-2.5 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-ink-faint">
              Conta de demonstração
            </p>
            <p className="mt-1 text-xs text-ink-soft">
              <span className="font-mono">recrutamento@techmoz.co.mz</span>
              <span className="mx-1.5 text-ink-faint">·</span>
              <span className="font-mono">Recruta@123</span>
            </p>
          </div>
        </form>

        {/* Rodapé legal */}
        <p className="mt-6 text-center text-[11px] text-ink-faint">
          © {new Date().getFullYear()} SIR — Sistema Inteligente de Recrutamento
        </p>
      </div>
    </div>
  );
}