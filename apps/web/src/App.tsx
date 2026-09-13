import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useLoad } from "./hooks";
import { api } from "./api";
import { APP_NAV_GROUPS, APP_ROUTES } from "./appRoutes";
import { DataSourceBadge } from "./components/Ui";

export default function App() {
  const { data: meta } = useLoad(() => api.meta());

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <small>YIJI XINJIE</small>
          <strong>一级芯界</strong>
          <div className="muted" style={{ color: "#9bb5aa", marginTop: 4 }}>
            AI Farm OS
          </div>
        </div>
        {APP_NAV_GROUPS.map((group) => (
          <nav key={group.title} className="nav-group">
            <h4>{group.title}</h4>
            {group.items.map((item) => (
              <NavLink key={item.path} to={item.path} className={({ isActive }) => (isActive ? "active" : "")}>
                {item.label}
                {"stub" in item && item.stub ? <span className="stub">STUB</span> : null}
              </NavLink>
            ))}
          </nav>
        ))}
      </aside>
      <div className="main">
        <div className="topbar">
          <div>
            <strong>{meta?.farm?.name ?? "一级芯界示范农场"}</strong>
            <div className="farm-meta">
              {meta?.farm?.location} · {meta?.season?.name ?? "本季"} · {meta?.line}
            </div>
          </div>
          <div className="legend">
            <DataSourceBadge source="REAL" />
            <DataSourceBadge source="SIMULATION" />
            <DataSourceBadge source="MANUAL" />
          </div>
        </div>
        <div className="content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            {APP_ROUTES.map((item) => (
              <Route key={item.path} path={item.path} element={<item.component />} />
            ))}
          </Routes>
        </div>
      </div>
    </div>
  );
}
