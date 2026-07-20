import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  ["/", "Chat"],
  ["/projects", "Projects"],
  ["/glossary", "Glossary"],
  ["/presets", "Presets"],
  ["/prompt", "Prompt preview"],
  ["/logs", "Logs"],
  ["/settings", "Settings"],
] as const;

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">TS</span>
        <span>Translation Studio</span>
      </div>
      <p className="eyebrow">JA to KO workspace</p>
      <nav>
        {navItems.map(([to, label]) => (
          <NavLink key={to} to={to} end={to === "/"}>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-foot">Middleware connected through local API</div>
    </aside>
  );
}

export function Layout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

export function PageHeader({ title, detail }: { title: string; detail: string }) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">TRANSLATION WORKSPACE</p>
        <h1>{title}</h1>
        <p className="muted">{detail}</p>
      </div>
    </header>
  );
}
