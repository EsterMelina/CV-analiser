import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Painel", end: true },
  { to: "/jobs", label: "Vagas" },
  { to: "/settings/email", label: "Integração de e-mail" },
];

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex min-h-screen flex-col bg-canvas text-ink md:h-screen md:flex-row">
      <aside className="w-full shrink-0 bg-surface border-b md:border-b-0 md:border-r border-line text-ink flex flex-col md:w-64">
        <div className="px-5 py-5 border-b border-line">
          <p className="font-display font-semibold text-lg leading-tight">Recrutamento</p>
          <p className="font-display font-semibold text-lg leading-tight text-ink-soft">Inteligente</p>
        </div>

        <nav aria-label="Navegação principal" className="flex flex-wrap gap-1 px-3 py-4 md:block md:flex-1 md:space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-sm px-3 py-2 text-sm transition-colors ${
                  isActive ? "bg-brand-soft text-brand-dark font-semibold" : "text-ink-soft hover:bg-canvas hover:text-ink"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-line text-sm">
          <p className="px-3 text-ink">{user?.name}</p>
          <p className="px-3 text-ink-soft text-xs mb-3">{user?.role === "admin" ? "Administrador" : "Recrutador"}</p>
          <button
            onClick={handleLogout}
            className="w-full text-left rounded-sm px-3 py-2 text-ink-soft hover:bg-canvas hover:text-ink transition-colors"
          >
            Terminar sessão
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1 md:overflow-y-auto">
        <header className="border-b border-line bg-surface px-5 py-4 sm:px-8"><p className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Gestão de pessoas <span className="mx-2 text-ink-faint">/</span> Recrutamento e selecção</p></header>
        <div className="max-w-6xl mx-auto px-4 py-6 sm:px-8 sm:py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
