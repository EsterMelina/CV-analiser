import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import "./Layout.css";

const NAV_ITEMS = [
  { to: "/",               label: "Painel",               icon: "dashboard", end: true },
  { to: "/jobs",           label: "Vagas",                icon: "work" },
  { to: "/settings/email", label: "Integração de e-mail", icon: "settings" },
];

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const pageTitle = pathname === "/"
    ? "Painel"
    : pathname === "/jobs/new"
    ? "Nova vaga"
    : pathname.includes("/applications/")
    ? "Perfil do candidato"
    : pathname.startsWith("/jobs/")
    ? "Detalhe da vaga"
    : pathname.startsWith("/jobs")
    ? "Vagas"
    : "Integração de e-mail";

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const initials =
    user?.name
      ?.split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("") ?? "?";

  return (
    <div className="sir-layout">
      {/* ===================== Sidebar ===================== */}
      <aside className="sir-sidebar">
        {/* Logo */}
        <div className="sir-sidebar__logo">
          <div className="sir-sidebar__logo-mark">
            <span className="sir-sidebar__link-icon">travel_explore</span>
          </div>
          <div className="sir-sidebar__logo-text">
            <span className="sir-sidebar__logo-title">SIR</span>
            <span className="sir-sidebar__logo-subtitle">Recrutamento IA</span>
          </div>
        </div>

        {/* Section label */}
        <div className="sir-sidebar__section">
          <div className="sir-sidebar__section-label">Plataforma</div>
        </div>

        {/* Nav */}
        <nav className="sir-sidebar__nav" aria-label="Navegação principal">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                "sir-sidebar__link" + (isActive ? " is-active" : "")
              }
            >
              <span className="sir-sidebar__link-icon">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Motor SIR IA */}
        <div className="sir-sidebar__card">
          <div className="sir-sidebar__card-title">
            <span className="sir-sidebar__link-icon" style={{ fontSize: 18 }}>
              verified
            </span>
            <span>Motor SIR IA</span>
          </div>
          <p className="sir-sidebar__card-text">
            Triagem preditiva com evidências empíricas ativada.
          </p>
        </div>

        {/* Utilizador + logout */}
        <div className="sir-sidebar__user">
          <div className="sir-sidebar__user-info">
            <div className="sir-sidebar__avatar">{initials}</div>
            <div className="sir-sidebar__user-text">
              <span className="sir-sidebar__user-name">{user?.name ?? "—"}</span>
              <span className="sir-sidebar__user-role">
                {user?.role === "admin" ? "Administrador" : "Recrutador"}
              </span>
            </div>
          </div>

          <button type="button" onClick={handleLogout} className="sir-sidebar__logout">
            <span className="sir-sidebar__link-icon" style={{ fontSize: 18 }}>
              logout
            </span>
            <span>Terminar sessão</span>
          </button>
        </div>
      </aside>

      {/* ===================== Conteúdo ===================== */}
      <div className="sir-main">
        {/* Header */}
        <header className="sir-header">
          <div className="sir-header__heading">
            <span className="sir-header__eyebrow">SIR · Recrutamento</span>
            <h2 className="sir-header__title">{pageTitle}</h2>
          </div>

          <div className="sir-header__actions">
            <div className="sir-header__pill">
              <span className="sir-header__pill-dot" />
              <span>Operação ativa</span>
            </div>
            {pathname !== "/jobs/new" && (
              <Link to="/jobs/new" className="sir-header__new-job">
                <span className="material-symbols-outlined" aria-hidden="true">add</span>
                <span>Nova vaga</span>
              </Link>
            )}
          </div>
        </header>

        {/* Main */}
        <main className="sir-content">
            <div className="sir-content__inner" key={pathname}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}